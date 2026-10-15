#!/usr/bin/env bash
pip3 install -r requirements.txt
[ -f .env ] || cp .env.example .env
