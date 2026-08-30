"""Cycle model for the two-source VC0/VC1 endpoint injection arbiter."""

from __future__ import annotations

from dataclasses import dataclass

from npu.sim.perf.noc_segmented_mesh import ModelFlit


@dataclass(frozen=True)
class EndpointVcArbiterCycle:
    cycle: int
    preferred_vc: int
    vc0_ready: bool
    vc1_ready: bool
    output: ModelFlit | None
    output_fire: bool
    protocol_error: bool
    dropped_vc0: bool
    dropped_vc1: bool


class EndpointVcInjectionArbiter:
    """Stateful ready/valid model matching the RTL arbiter exactly."""

    def __init__(self) -> None:
        self.cycle = 0
        self.preferred_vc = 0
        self.held_vc: int | None = None
        self.protocol_error = False

    def step(
        self,
        *,
        vc0: ModelFlit | None,
        vc1: ModelFlit | None,
        out_ready: bool,
    ) -> EndpointVcArbiterCycle:
        dropped_vc0 = vc0 is not None and vc0.vc != 0
        dropped_vc1 = vc1 is not None and vc1.vc != 1
        eligible = {
            0: vc0 if vc0 is not None and not dropped_vc0 else None,
            1: vc1 if vc1 is not None and not dropped_vc1 else None,
        }
        held_source_dropped = (
            (self.held_vc == 0 and dropped_vc0)
            or (self.held_vc == 1 and dropped_vc1)
        )
        selected_vc: int | None = None
        if self.held_vc is not None:
            if eligible[self.held_vc] is not None:
                selected_vc = self.held_vc
        else:
            for candidate in (self.preferred_vc, 1 - self.preferred_vc):
                if eligible[candidate] is not None:
                    selected_vc = candidate
                    break
        output = None if selected_vc is None else eligible[selected_vc]
        output_fire = output is not None and out_ready
        result = EndpointVcArbiterCycle(
            cycle=self.cycle,
            preferred_vc=self.preferred_vc,
            vc0_ready=dropped_vc0 or (selected_vc == 0 and out_ready),
            vc1_ready=dropped_vc1 or (selected_vc == 1 and out_ready),
            output=output,
            output_fire=output_fire,
            protocol_error=self.protocol_error,
            dropped_vc0=dropped_vc0,
            dropped_vc1=dropped_vc1,
        )
        if dropped_vc0 or dropped_vc1:
            self.protocol_error = True
        if held_source_dropped:
            self.held_vc = None
        elif output_fire:
            self.held_vc = None
            self.preferred_vc = 1 - int(selected_vc)
        elif output is not None and not out_ready:
            self.held_vc = selected_vc
        self.cycle += 1
        return result


__all__ = ["EndpointVcArbiterCycle", "EndpointVcInjectionArbiter"]
