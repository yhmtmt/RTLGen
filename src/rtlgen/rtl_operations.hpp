#pragma once

#include "config.hpp"

void emitMcmModule(const McmOperationConfig &config, const OperandDefinition &operand);
void emitCmvmModule(const CmvmOperationConfig &config, const OperandDefinition &operand);
void emitActivationModule(const ActivationOperationConfig &config, const OperandDefinition &operand);
void emitSoftmaxRowwiseModule(const SoftmaxRowwiseOperationConfig &config, const OperandDefinition &operand);
void emitBf16RecipNormModule(const Bf16RecipNormOperationConfig &config, const OperandDefinition &operand);
void emitScoreTieRankModule(const ScoreTieRankOperationConfig &config, const OperandDefinition &operand);
