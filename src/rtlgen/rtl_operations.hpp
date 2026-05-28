#pragma once

#include "config.hpp"

void emitMcmModule(const McmOperationConfig &config, const OperandDefinition &operand);
void emitCmvmModule(const CmvmOperationConfig &config, const OperandDefinition &operand);
void emitActivationModule(const ActivationOperationConfig &config, const OperandDefinition &operand);
void emitSoftmaxRowwiseModule(const SoftmaxRowwiseOperationConfig &config, const OperandDefinition &operand);
void emitBf16RecipNormModule(const Bf16RecipNormOperationConfig &config, const OperandDefinition &operand);
void emitScoreTieRankModule(const ScoreTieRankOperationConfig &config, const OperandDefinition &operand);
void emitLogitRankModule(const LogitRankOperationConfig &config, const OperandDefinition &operand);
void emitCandidateStreamMergeFifoModule(const CandidateStreamMergeFifoOperationConfig &config,
                                        const OperandDefinition &operand);
void emitAttentionKvTileModule(const AttentionKvTileOperationConfig &config,
                               const OperandDefinition &operand);
void emitAttentionKvReducerModule(const AttentionKvReducerOperationConfig &config,
                                  const OperandDefinition &operand);
void emitAttentionKvReducerTreeModule(const AttentionKvReducerTreeOperationConfig &config,
                                      const OperandDefinition &operand);
void emitAttentionKvReducerFoldedModule(const AttentionKvReducerFoldedOperationConfig &config,
                                        const OperandDefinition &operand);
