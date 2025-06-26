#!/bin/bash
cd /home/kavia/workspace/code-generation/resumematch-ai-73807-35a6cda2/resume_analyzer_backend_workspace/resume_analyzer_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

