{ pkgs ? import ./nix {} }:
let 
  pythonPackages = with pkgs.python38Packages; [poetry libcloud numpy ipython matplotlib pyyaml ];
in
  pkgs.mkShell {
    buildInputs = with pkgs; [
      niv.niv
    ] ++ pythonPackages;
  }
