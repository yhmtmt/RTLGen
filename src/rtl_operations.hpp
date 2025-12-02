#pragma once

#include "config.hpp"

void emitMcmModule(const McmOperationConfig &config, const OperandDefinition &operand);
void emitCmvmModule(const CmvmOperationConfig &config, const OperandDefinition &operand);
void emitActivationModule(const ActivationOperationConfig &config, const OperandDefinition &operand);
