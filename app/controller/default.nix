{ pkgs ? import ../../nix { } }:
pkgs.poetry2nix.mkPoetryApplication {
  projectDir = ./.;
}
