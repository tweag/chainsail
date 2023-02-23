{ pkgs ? import ../../nix {
  overlays = [
    (import ~/Code/nix-community/poetry2nix/overlay.nix)
  ];
} }:
pkgs.poetry2nix.mkPoetryApplication {
  projectDir = ./.;
}
