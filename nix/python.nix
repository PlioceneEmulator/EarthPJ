pkgs: self: super: rec {
  metpy = self.buildPythonPackage rec {
    pname = "MetPy";
    version = "1.0.1";
    src = self.fetchPypi {
      inherit pname version;
      sha256 = "sha256-FvqYBvrMJPMfRUuJh0HsVjmnK6nU/4oZrQ6UYp2Ty5U=";
    };
    propagatedBuildInputs = with self; [
      matplotlib
      numpy
      pandas
      pint
      pooch
      pyproj
      scipy
      traitlets
      xarray
      importlib-resources
      importlib-metadata
    ];
    # The setuptools checks try to use the network which isn't allowed
    # during the Nix build. Disabling them for now.
    doCheck = false;
  };

  # cmaps = buildPythonPackage rec {
  #   pname = "cmaps";
  #   version = "0.1.0";
  #   src = fetchPypi {
  #     inherit pname version;
  #     sha256 = "sha256-FvqYBvrMJPMfRUuJh0HsVjmnK6nU/4oZrQ6UYp2Ty5U=";
  #   };
  #   # meta = with pkgs.stdenv.lib; {
  #   #   description = "Colormaps for scientific visualization.";
  #   #   homepage = "https://github.com/hhuangwx/cmaps";
  #   #   license = licenses.mit;
  #   #   maintainers = [maintainers.yourname];
  #   # };
  # };

  geocat = buildPythonPackage rec {
    pname = "geocat.viz";
    version = "0.9.1";
    src = fetchPypi {
      inherit pname version;
      sha256 = "1hkyw2avwpj2f1qx2d2v9pf9xxr8r6f3j0bwq3l3gzb6w8ayppj1";
    };
  };
}
