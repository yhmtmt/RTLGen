import json
from pathlib import Path
import shutil
import subprocess

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.db import create_all
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.l1_task_generator import (
    Layer1SweepGenerateRequest,
    _read_config_target,
    generate_l1_sweep_task,
)
from npu.eval.check_attention_exact_partial_physical_calibration_guard import (
    main as guard_main,
)
from npu.rtlgen.gen_attention_exact_partial_async_fifo_physical_harness import (
    generate as generate_cdc,
)
from npu.rtlgen.gen_attention_score32_exact_partial_temporal_finalizer_physical_harness import (
    generate as generate_temporal_finalizer,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_ID = "prop_l1_decoder_attention_exact_partial_physical_calibration_v1"
TEMPORAL_DESIGNS = [
    f"attention_score32_exact_partial_temporal_finalizer_physical_l{lanes}"
    for lanes in (1, 2, 4, 8)
]
CDC_DESIGNS = [
    "attention_exact_partial_async_fifo_d4_source_domain_physical",
    "attention_exact_partial_async_fifo_d4_destination_domain_physical",
]


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    pytest.skip(f"{name} unavailable")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _lint(top: str, rtl: Path, *, macros: bool) -> None:
    command = [
        _tool("verilator"),
        "--lint-only",
        "-Wno-WIDTHEXPAND",
        "-Wno-WIDTHTRUNC",
        "-Wno-UNUSEDSIGNAL",
        "-Wno-UNDRIVEN",
        "-Wno-TIMESCALEMOD",
        "-Wno-SIDEEFFECT",
        "-Wno-LATCH",
        "-Wno-UNOPTFLAT",
        "-Wno-MULTIDRIVEN",
        "--top-module",
        top,
        str(rtl),
    ]
    if macros:
        command.append(str(REPO_ROOT / "npu/rtl/fakeram45_64x32_blackbox.v"))
    result = subprocess.run(command, capture_output=True, text=True, timeout=240)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("lanes", [1, 2, 4, 8])
def test_temporal_finalizer_generator_is_narrow_and_macro_backed(
    tmp_path: Path, lanes: int
) -> None:
    top = f"calibration_l{lanes}"
    config = {
        "top_name": top,
        "attention_score32_exact_partial_temporal_finalizer_physical_harness": {
            "divider_lanes": lanes,
            "heads": 2,
            "windows": 2,
        },
    }
    generate_temporal_finalizer(config, tmp_path)
    rtl = (tmp_path / "top.v").read_text(encoding="utf-8")
    manifest = _load(
        tmp_path
        / "attention_score32_exact_partial_temporal_finalizer_physical_harness_manifest.json"
    )
    macros = _load(tmp_path / "macro_manifest.json")

    assert manifest["divider_lanes"] == lanes
    assert manifest["top_pin_bits"] == 388
    assert manifest["macro_count"] == 104
    assert manifest["whole_dual_clock_common_delay_claim"] is False
    assert macros["blackboxes"] == ["fakeram45_64x32"]
    assert macros["manifest_params"]["macro_count"] == 104
    assert "fakeram45_64x32 u_state_mem" in rtl
    assert "state_global_max_q [0:" not in rtl
    assert "reg [393:0] state" not in rtl
    assert "localparam integer SOURCE_BEATS = 64;" in rtl
    assert "localparam integer FINAL_BEATS = 32;" in rtl
    _lint(top, tmp_path / "top.v", macros=True)


@pytest.mark.parametrize("domain", ["source", "destination"])
def test_cdc_generator_is_selected_domain_only(
    tmp_path: Path, domain: str
) -> None:
    top = f"cdc_{domain}"
    config = {
        "top_name": top,
        "attention_exact_partial_async_fifo_physical_harness": {
            "depth": 4,
            "timed_domain": domain,
        },
    }
    generate_cdc(config, tmp_path)
    rtl = (tmp_path / "top.v").read_text(encoding="utf-8")
    manifest = _load(
        tmp_path / "attention_exact_partial_async_fifo_physical_harness_manifest.json"
    )

    assert manifest["payload_bits"] == 464
    assert manifest["depth"] == 4
    assert manifest["timed_domain"] == domain
    assert manifest["top_pin_bits"] == 292
    assert manifest["whole_dual_clock_common_delay_claim"] is False
    assert manifest["cross_domain_paths_are_signoff_timing"] is False
    assert "reg [463:0] mem [0:DEPTH-1];" in rtl
    assert "helper_clk_q <= ~helper_clk_q;" in rtl
    _lint(top, tmp_path / "top.v", macros=False)


def test_checked_designs_guards_sweeps_and_task_commands(tmp_path: Path) -> None:
    for design in TEMPORAL_DESIGNS + CDC_DESIGNS:
        source_dir = REPO_ROOT / "runs/designs/npu_blocks" / design
        config = _load(source_dir / "config.json")
        macro = _load(source_dir / "macro_manifest.json")
        assert config["report_links"]["proposal_id"] == PROPOSAL_ID
        assert macro["module"] == design

        copied = tmp_path / "runs/designs/npu_blocks" / design
        copied.mkdir(parents=True)
        shutil.copy2(source_dir / "config.json", copied / "config.json")
        shutil.copy2(source_dir / "macro_manifest.json", copied / "macro_manifest.json")
        generator = (
            generate_temporal_finalizer if design in TEMPORAL_DESIGNS else generate_cdc
        )
        generator(config, copied / "verilog")
        assert guard_main(["--design-dir", str(copied)]) == 0

        target = _read_config_target(
            source_dir / "config.json",
            repo_root=REPO_ROOT,
            config_rel=str((source_dir / "config.json").relative_to(REPO_ROOT)),
            out_root="runs/designs/npu_blocks",
            make_target=None,
        )
        names = [command["name"] for command in target.commands]
        assert names[1] == "check_attention_exact_partial_physical_calibration_guard"
        assert "run_block_sweep" == names[2]
        if design in TEMPORAL_DESIGNS:
            assert "--macro_manifest" in target.commands[2]["run"]
        else:
            assert "--macro_manifest" not in target.commands[2]["run"]

    temporal_sweep = _load(
        REPO_ROOT
        / "runs/campaigns/npu/attention_exact_partial_physical_calibration_v1/"
        "sweeps/nangate45_temporal_finalizer_macro.json"
    )["flow_params"]
    assert temporal_sweep["CLOCK_PERIOD"] == [6.0, 8.0, 10.0, 12.0]
    assert temporal_sweep["DIE_AREA"] == ["0 0 1600 1600"]
    assert temporal_sweep["CORE_AREA"] == ["50 50 1550 1550"]
    assert temporal_sweep["PLACE_DENSITY"] == [0.4]
    assert temporal_sweep["SYNTH_HIERARCHICAL"] == [1]

    request = _load(
        REPO_ROOT
        / f"docs/proposals/{PROPOSAL_ID}/evaluation_requests.json"
    )
    assert [item["item_id"] for item in request["requested_items"]] == [
        "l1_decoder_attention_exact_partial_temporal_finalizer_physical_calibration_v1",
        "l1_decoder_attention_exact_partial_async_fifo_domain_physical_calibration_v1",
    ]
    assert "source_requirement.required_sha" in request["source_commit_note"]


def test_normal_task_mechanism_attaches_required_source_commit() -> None:
    source_commit = subprocess.run(
        ["git", "rev-parse", "origin/master"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
        text=True,
    ).stdout.strip()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    config_paths = [
        f"runs/designs/npu_blocks/{design}/config.json"
        for design in TEMPORAL_DESIGNS
    ]
    with Session(engine) as session:
        result = generate_l1_sweep_task(
            session,
            Layer1SweepGenerateRequest(
                repo_root=str(REPO_ROOT),
                sweep_path=(
                    "runs/campaigns/npu/attention_exact_partial_physical_calibration_v1/"
                    "sweeps/nangate45_temporal_finalizer_macro.json"
                ),
                config_paths=config_paths,
                platform="nangate45",
                out_root="runs/designs/npu_blocks",
                requested_by="@developer",
                source_commit=source_commit,
                item_id=(
                    "l1_decoder_attention_exact_partial_temporal_finalizer_"
                    "physical_calibration_v1"
                ),
                proposal_id=PROPOSAL_ID,
                update_proposal_files=False,
            ),
        )
        work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
        task_request = session.query(TaskRequest).filter_by(id=work_item.task_request_id).one()
        assert work_item.source_commit == source_commit
        assert task_request.source_commit == source_commit
        assert task_request.request_payload["source_requirement"]["required_sha"] == source_commit
        assert len(work_item.command_manifest) == 18
        assert all(
            "--macro_manifest" in command["run"]
            for command in work_item.command_manifest
            if command["name"].startswith("run_block_sweep_")
        )


def test_temporal_finalizer_self_traffic_completes_without_protocol_error(
    tmp_path: Path,
) -> None:
    if not (shutil.which("iverilog") and shutil.which("vvp")):
        pytest.skip("iverilog/vvp unavailable")
    config = _load(
        REPO_ROOT
        / "runs/designs/npu_blocks/"
        "attention_score32_exact_partial_temporal_finalizer_physical_l8/config.json"
    )
    generate_temporal_finalizer(config, tmp_path)
    tb = tmp_path / "tb.v"
    tb.write_text(
        """`timescale 1ns/1ps
module tb;
reg clk=0; always #5 clk=~clk;
reg rst_n=0, start=0; reg [31:0] seed=32'h12345678;
wire done; wire [31:0] protocol_error_count;
wire [31:0] folded_result, cycle_count, source_accepted_count;
wire [31:0] temporal_emitted_count, finalizer_completed_count;
wire [31:0] state_request_count, state_read_count, state_write_count;
wire [31:0] state_stall_count, output_stall_count;
attention_score32_exact_partial_temporal_finalizer_physical_l8 dut(.*);
initial begin
  repeat(4) @(posedge clk); rst_n <= 1;
  repeat(2) @(posedge clk); start <= 1;
  @(posedge clk); start <= 0;
  wait(done); @(posedge clk);
  if(source_accepted_count != 64 || temporal_emitted_count != 32
      || finalizer_completed_count != 32 || protocol_error_count != 0)
    $fatal(1, "invalid physical-harness self traffic");
  $finish;
end
initial begin #1000000; $fatal(1, "timeout"); end
endmodule
""",
        encoding="utf-8",
    )
    simv = tmp_path / "simv"
    compile_result = subprocess.run(
        [
            _tool("iverilog"),
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(simv),
            str(tmp_path / "top.v"),
            str(REPO_ROOT / "npu/sim/rtl/fakeram45_64x32_model.sv"),
            str(tb),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert compile_result.returncode == 0, compile_result.stderr
    run_result = subprocess.run(
        [_tool("vvp"), str(simv)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert run_result.returncode == 0, run_result.stdout + run_result.stderr
