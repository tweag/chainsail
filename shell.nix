{ pkgs ? import ./nix {} }:
let 
  pythonPackages = with pkgs.python38Packages; [ poetry ];
in
  pkgs.mkShell {
    buildInputs = with pkgs; [
      niv.niv
    ] ++ pythonPackages;
  }
