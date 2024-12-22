{
    description = "A configurable program to create ascii art";
    outputs = {
        self
        , nixpkgs
        , ...
    }: let
        forAll = with nixpkgs.lib; (f:
            genAttrs systems.flakeExposed (system: let
                pkgs = import nixpkgs { 
                    inherit system;
                };
            in
            f pkgs
        ));
        pythonEnvPackage = (pkgs: 
            pkgs.python3.withPackages(p: with p; [
                opencv4
                numpy
            ])
        );
    in {
        devShells = forAll (pkgs: let
            pyEnv = pythonEnvPackage pkgs;
        in {
            default = pkgs.mkShell {
                nativeBuildInputs = [
                    pyEnv
                ];
                PYTHONPATH="${pyEnv}/${pyEnv.sitePackages}";
            };
        });
    };
}
