#!/bin/bash
cd /home/kavia/workspace/code-generation/resumematch-ai-73807-35a6cda2/resume_analyzer_frontend_workspace/resume_analyzer_frontend
npm run build
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
   exit 1
fi

