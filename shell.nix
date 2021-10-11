{ pkgs ? import ./nix {} }:
with pkgs.python38Packages;
let
  black = buildPythonPackage rec {
    pname = "black";
    version = "20.8b1";
    src = fetchPypi {
      inherit version pname;
      sha256 = "1c02557aa099101b9d21496f8a914e9ed2222ef70336404eeeac8edba836fbea";
    };
    buildInputs = [
      setuptools_scm
      regex
      click
      pathspec
      typed-ast
      toml
      mypy-extensions
      appdirs
      typing-extensions
    ];
    propagatedBuildInputs = [
      regex
      typing-extensions
      mypy-extensions
      toml
      typed-ast
      pathspec
      ];
    doCheck = false;
  };
in 
  pkgs.mkShell {
    buildInputs = with pkgs; [
      python38
      poetry # version 1.1.10 (required) while pythonPackages38.poetry is lower
      black
      niv.niv
      yarn
      nodejs
      docker-compose
      openmpi
      python38Packages.tkinter
      ncurses
      file
    ];
    # Setting the LD_LIBRARY_PATH environment variable.
    # Can also make use of the `.overrideAttrs` medthod to prevent from overwriting it (See PR #310 for details)
    LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.file}/lib";
  }
  