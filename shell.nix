{ pkgs ? import ./nix {} }:
let 
  pythonPackages = with pkgs.python38Packages; [poetry libcloud numpy ipython matplotlib ];
in
  pkgs.mkShell {
    buildInputs = with pkgs; [
      niv.niv
    ] ++ pythonPackages;
  }
