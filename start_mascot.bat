@echo off
:: Pythonのパスを確認し、適切に設定してください
set PYTHON_PATH=python

:: スクリプトのディレクトリに移動
cd /d c:\temp\desktop\mascot

:: 必要な依存関係をインストール
::%PYTHON_PATH% -m pip install -r requirements.txt

:: mascot_system.py を実行
%PYTHON_PATH% mascot_system.py

:: 終了時に一時停止
pause
