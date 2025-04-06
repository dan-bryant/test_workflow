# filename: .github/workflows/bld_cmd_ci.yml
name: Build with CMD and CI on VS
run-name: bld-cmd-ci-vs${{ github.event.inputs.vs_year }}-${{ github.event.inputs.architecture }}-${{ github.event.inputs.target }}-Py_${{ github.event.inputs.python_version }}-Hack_${{ github.event.inputs.hack }}

on:
  workflow_dispatch:  # Allows the workflow to be triggered manually
    inputs:
      hack:
        description: "Enable HACK mode"
        required: false
        default: "false"
      full:
        description: "Build the most targets"
        required: false
        default: "true"
      vs_year:
        description: "Visual Studio Year ( 22 | 19 | 15 )"
        required: false
        default: "22"
      target:
        description: "Build target (DEBUG | RELEASE)"
        required: false
        default: "RELEASE"
      architecture:
        description: "Build architecture (X64 | IA32 | AARM64)"
        required: false
        default: "X64"
      python_version:
        description: "Python version to use"
        required: false
        default: "3.12.9"

jobs:
  build:
    # Use the Windows Server 2022 runner
    runs-on: windows-20${{ github.event.inputs.vs_year }}
    # https://docs.github.com/en/actions/writing-workflows
    #  /choosing-what-your-workflow-does
    #  /accessing-contextual-information-about-workflow-runs
    env:
      GH_WORKSPACE: ${{ github.workspace }}
      GH_HEAD_SHA: ${{ github.sha }}
      IASL_PREFIX: C:\ProgramData\chocolatey\bin\
      CLANG_BIN: C:\Program Files\LLVM\bin\
      NASM_PREFIX: C:\Program Files\NASM\
      PYTHON_COMMAND: D:\Python${{ github.event.inputs.python_version }}\python.exe
      PYTHON_PATH: D:\Python${{ github.event.inputs.python_version }}
      PYTHON_VERSION: ${{ github.event.inputs.python_version }}
      PYTHON_SETUP: python-${{ github.event.inputs.python_version }}-amd64.exe
      STUART: D:\Python${{ github.event.inputs.python_version }}\Scripts\stuart
      GH_REPO_URL: ${{ github.server_url }}/${{ github.repository }}
      GH_WORKFLOW_NAME: ${{ github.workflow }}
      BUILD_BAT: mk_bat.py
      REPO_PATH: D:\r
      EDK2_PATH: D:\r\Edk2
      ARTIFACT_PATH: D:\artifact
      EMU_HOST: WinHost
      CHAIN: VS20${{ github.event.inputs.vs_year }}
      ARCH: ${{ github.event.inputs.architecture }}
      TRGT: ${{ github.event.inputs.target }}

    defaults:
      run:
        shell: cmd
    steps:
      - name: List Environment Variables
        run: set

      - name: Clone Repo
        run: git clone --recurse-submodules --depth 1 --shallow-submodules %GH_REPO_URL% %REPO_PATH%

      # - name: Checkout Repository recursively with long-files
      #   uses: actions/checkout@v4
      #   with:
      #     submodules: recursive     # Initialize and update submodules
      #     long-paths: true          # Enable long path support

      - name: Install Python 3.12.9, NASM, IASL
        # if: ${{ github.event.inputs.hack != 'true' }}
        run: |
          curl -o ${{ github.workspace }}\%PYTHON_SETUP% https://www.python.org/ftp/python/%PYTHON_VERSION%/%PYTHON_SETUP%
          ${{ github.workspace }}\%PYTHON_SETUP% /quiet TargetDir=%PYTHON_PATH%
          choco install nasm iasl -y

      - name: Install Pip Requirements
        if: ${{ github.event.inputs.hack != 'true' }}
        run: |
          %PYTHON_COMMAND% -m pip install --upgrade pip
          %PYTHON_COMMAND% -m pip install -r "%EDK2_PATH%\pip-requirements.txt"

      - name: Build BaseTools
        if: ${{ github.event.inputs.hack != 'true' }}
        run: |
          pushd "%EDK2_PATH%"
          call edksetup.bat Reconfig %CHAIN%
          %PYTHON_COMMAND% BaseTools\Edk2ToolsBuild.py -t %CHAIN%

      - name: Setup and update Edk2
        if: ${{ github.event.inputs.hack != 'true' }}
        run: |
          pushd "%EDK2_PATH%"
          call edksetup.bat Reconfig %CHAIN%
          %STUART%_setup -c .pytool\CISettings.py -a %ARCH% -t %TRGT% TOOL_CHAIN_TAG=%CHAIN%
          %STUART%_update -c .pytool\CISettings.py -a %ARCH% -t %TRGT% TOOL_CHAIN_TAG=%CHAIN%

      - name: Build Edk2
        # Compiler #2065: EmbeddedPkg\...\VirtualRealTimeClockLib.c(89): 'BUILD_EPOCH': undeclared
        continue-on-error: true
        if: ${{ github.event.inputs.full == 'true' && github.event.inputs.hack != 'true' }}
        run: |
          pushd "%EDK2_PATH%"
          call edksetup.bat Reconfig %CHAIN%
          %STUART%_ci_build -c .pytool\CISettings.py -a %ARCH% -t %TRGT% TOOL_CHAIN_TAG=%CHAIN%

      - name: Setup and update EmulatorPkg
        if: ${{ github.event.inputs.hack != 'true' }}
        run: |
          pushd "%EDK2_PATH%"
          call edksetup.bat Reconfig %CHAIN%
          %STUART%_setup -c EmulatorPkg\PlatformCI\PlatformBuild.py -a %ARCH% -t %TRGT% TOOL_CHAIN_TAG=%CHAIN%
          %STUART%_update -c EmulatorPkg\PlatformCI\PlatformBuild.py -a %ARCH% -t %TRGT% TOOL_CHAIN_TAG=%CHAIN%

      - name: Build EmulatorPkg
        if: ${{ github.event.inputs.hack != 'true' }}
        run: |
          pushd "%EDK2_PATH%"
          call edksetup.bat Reconfig %CHAIN%
          %STUART%_build -c EmulatorPkg\PlatformCI\PlatformBuild.py -a %ARCH% TOOL_CHAIN_TAG=%CHAIN% TARGET=%TRGT%

      - name: Setup and update OvmfPkg
        if: ${{ github.event.inputs.hack != 'true' }}
        run: |
          pushd "%EDK2_PATH%"
          call edksetup.bat Reconfig %CHAIN%
          %STUART%_setup -c OvmfPkg\PlatformCI\PlatformBuild.py -a %ARCH% -t %TRGT% TOOL_CHAIN_TAG=%CHAIN%
          %STUART%_update -c OvmfPkg\PlatformCI\PlatformBuild.py -a %ARCH% -t %TRGT% TOOL_CHAIN_TAG=%CHAIN%

      - name: Build OvmfPkg
        if: ${{ github.event.inputs.hack != 'true' }}
        run: |
          pushd "%EDK2_PATH%"
          call edksetup.bat Reconfig %CHAIN%
          %STUART%_build -c OvmfPkg\PlatformCI\PlatformBuild.py -a %ARCH% TOOL_CHAIN_TAG=%CHAIN% TARGET=%TRGT%

      - name: Gather VS Environment Data
        run: |
          set VOLUME=%ARTIFACT_PATH%\Emulator%ARCH%\%TRGT%_%CHAIN%\%ARCH%\%EMU_HOST%
          pushd "%EDK2_PATH%"
          call edksetup.bat Reconfig %CHAIN%
          pushd "%VOLUME%"
          set > vmInfoEnvVars.txt
          vswhere -format json > vmInfoVswhere.json
          jq -r ".[0].properties.setupEngineFilePath" vmInfoVswhere.json > vmInfoVsSetupTool.txt
          for /f "delims=;" %%p in (vmInfoVsSetupTool.txt) do (
            set VS_SETUP_PATH=%%~dpp
          )
          jq -r ".[0].installationPath" vmInfoVswhere.json > vmInfoVsInstallPath.txt
          for /f "delims=;" %%p in (vmInfoVsInstallPath.txt) do (
            echo.| "%VS_SETUP_PATH%\vs_installer.exe" export --quiet --installPath "%%p" --config vmInfoVsConfig.json
          )

      - name: Package Build Outputs
        # Robocopy will likely throw an error on one of these, so ignore and continue
        continue-on-error: true
        run: |
          set VOLUME=%ARTIFACT_PATH%\Emulator%ARCH%\%TRGT%_%CHAIN%\%ARCH%\%EMU_HOST%
          pushd "%EDK2_PATH%\Build"
          echo "%CD%"
          robocopy %REPO_PATH%\.github\workflows "%ARTIFACT_PATH%" *.yml
          for /d %%p in (. *) do (
            robocopy "%EDK2_PATH%\Build\%%p" "%ARTIFACT_PATH%\%%p" vmInfo*
            robocopy "%EDK2_PATH%\Build\%%p" "%ARTIFACT_PATH%\%%p" BUILDLOG*.txt
            robocopy "%EDK2_PATH%\Build\%%p" "%ARTIFACT_PATH%\%%p" *LOG.txt
            robocopy "%EDK2_PATH%\Build\%%p\All\%TRGT%_%CHAIN%\%ARCH%" "%ARTIFACT_PATH%\%%p\%TRGT%_%CHAIN%\%ARCH%" *.efi
            robocopy "%EDK2_PATH%\Build\%%p\%TRGT%_%CHAIN%\%ARCH%" "%ARTIFACT_PATH%\%%p\%TRGT%_%CHAIN%\%ARCH%" *.efi
            robocopy "%EDK2_PATH%\Build\%%p\%TRGT%_%CHAIN%\%ARCH%" "%ARTIFACT_PATH%\%%p\%TRGT%_%CHAIN%\%ARCH%" %EMU_HOST%*
            robocopy "%EDK2_PATH%\Build\%%p\%TRGT%_%CHAIN%\FV" "%ARTIFACT_PATH%\%%p\%TRGT%_%CHAIN%\FV" *
          )

      - name: Build UEFI Volume
        run: |
          set VOLUME=%ARTIFACT_PATH%\Emulator%ARCH%\%TRGT%_%CHAIN%\%ARCH%\%EMU_HOST%
          pushd %ARTIFACT_PATH%
          echo %GH_HEAD_SHA% > vmInfo%CHAIN%-%ARCH%-%TRGT%-Py%PYTHON_VERSION%.txt
          dir /s /b /a:-d > repoFileListing.txt
          dir /s /b /a:d > repoDirListing.txt
          findstr /m /c:"%GH_WORKFLOW_NAME%" .github\workflows\*.yml > repoWorkflowFile.txt
          for /f "delims=;" %%p in (repoWorkflowFile.txt) do (
            set GH_WORKFLOW_FILE=%%~dpp
          )
          set BAT_FILE=build%CHAIN%-%ARCH%-%TRGT%-Py%PYTHON_VERSION%.bat
          %PYTHON_COMMAND% %REPO_PATH%\%BUILD_BAT% %GH_WORKFLOW_FILE% %BAT_FILE%
          echo efiVolume: %VOLUME%>> README.txt
          echo gitTag: %GH_HEAD_SHA%>> README.txt
          echo workflowFile: %GH_WORKFLOW_FILE%>> README.txt
          echo batFile: %BAT_FILE%>> README.txt
          mkdir %VOLUME%\EFI\Boot
          mkdir %VOLUME%\EFI\Tools
          for /d %%p in (*) do (
            robocopy "%ARTIFACT_PATH%\%%p\%TRGT%_%CHAIN%\%ARCH%" "%VOLUME%\EFI\Tools" *.efi /XO
          )
          copy %VOLUME%\EFI\Tools\Shell.efi %VOLUME%\EFI\Boot\bootx64.efi
          move %VOLUME%\..\%EMU_HOST%* %VOLUME%

      # filename: .github/workflows/bld_cmd_ci_vs22.yml
      - name: Upload Artifact
        uses: actions/upload-artifact@v4
        with:
          name: bld-cmd-ci-vs${{ github.event.inputs.vs_year }}-${{ github.event.inputs.architecture }}-${{ github.event.inputs.target }}-Py_${{ github.event.inputs.python_version }}-Hack_${{ github.event.inputs.hack }}
          path: ${{ env.ARTIFACT_PATH }}\**\*

