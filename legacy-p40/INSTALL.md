# Strata Legacy GPU

Windows x64. This build targets NVIDIA Pascal (Tesla P40, `sm_61`) and CPUs with AVX, including Ivy Bridge. Install a CUDA 12.9-compatible NVIDIA driver and the [Microsoft Visual C++ v14 x64 runtime](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist). The installer contains the engine, Python and CUDA libraries. Supply the two Swift 1.5 IQ3_S GGUF shards separately.

```bat
CONFIGURE.cmd "D:\Models\Swift-IQ3_S"
START.cmd
```

If you have a prepared Q2 MTP pack, append `--mtp-dir "D:\Models\Swift-MTP\rt"` to `CONFIGURE.cmd`. The projector is loaded on the CPU when `mmproj-Qwen3.8-Flash-Next-BF16.gguf` is present. The API listens at `http://127.0.0.1:8093/v1`. `STOP.cmd` requests graceful shutdown. Enable launch at Windows sign-in with `powershell -ExecutionPolicy Bypass -File tools\autostart.ps1`. Use `-Disable` to remove that entry.

To build the engine from this checkout, run `legacy-p40/build.ps1` from an x64 Visual Studio Developer PowerShell with CMake, Ninja and CUDA 12.9. The engine is written to `build-p40/strata.exe`.

## Установка

Сборка для Windows x64, Tesla P40 (`sm_61`) и процессоров с AVX, включая Ivy Bridge. Нужны драйвер NVIDIA с поддержкой CUDA 12.9 и [Microsoft Visual C++ v14 x64](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist). Установщик содержит движок, Python и библиотеки CUDA. Два шарда GGUF модели Swift 1.5 IQ3_S укажите отдельно.

Выполните команды выше из папки установки. Параметр `--mtp-dir` принимает папку готового Q2 MTP. Если рядом с шардами есть `mmproj-Qwen3.8-Flash-Next-BF16.gguf`, Strata использует CPU для изображений. `STOP.cmd` штатно завершает работу. Скрипт `tools\autostart.ps1` включает запуск при входе в Windows, `-Disable` отключает его.

Для сборки движка из репозитория запустите `legacy-p40/build.ps1` в x64 Visual Studio Developer PowerShell с CMake, Ninja и CUDA 12.9. Результат — `build-p40/strata.exe`.
