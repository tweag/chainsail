let
  lock = builtins.fromJSON (builtins.readFile ../flake.lock);
  inherit (lock.nodes.nixpkgs.locked) rev narHash;
  nixpkgs = fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/${rev}.tar.gz";
    sha256 = narHash;
  };
in
import nixpkgs
