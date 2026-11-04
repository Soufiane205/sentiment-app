"""Vérifie la roue dans un environnement neuf, depuis un dossier temporaire (TP6).

Usage : python scripts/check_wheel.py dist/paquet.whl --model models/sentiment.joblib
--reuse-dependencies permet une vérification locale sans réseau ; la CI n'utilise pas cette option.
"""
import argparse
import json
import os
import subprocess
import sysconfig
import tempfile
import venv
from pathlib import Path
from zipfile import ZipFile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--reuse-dependencies", action="store_true")
    args = parser.parse_args()
    wheel, model = args.wheel.resolve(), args.model.resolve()
    if not wheel.is_file() or not model.is_file():
        parser.error("la roue et le modèle doivent exister")

    with ZipFile(wheel) as archive:
        names = archive.namelist()
        packages = {name.split("/")[0] for name in names if ".dist-info/" not in name}
        assert packages == {"sentiment_app", "api", "ui"}, packages
        assert not any(name.endswith((".joblib", ".pyc")) for name in names)
        metadata = next(name for name in names if name.endswith(".dist-info/METADATA"))
        version = next(line[9:] for line in archive.read(metadata).decode().splitlines()
                       if line.startswith("Version: "))
    print("Contenu : sentiment_app, api et ui ; aucun test, donnée ou modèle.", flush=True)

    with tempfile.TemporaryDirectory(prefix="sentiment-tp6-") as directory:
        outside = Path(directory).resolve()
        environment = outside / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        binaries = environment / ("Scripts" if os.name == "nt" else "bin")
        python = binaries / ("python.exe" if os.name == "nt" else "python")
        command = binaries / ("sentiment.exe" if os.name == "nt" else "sentiment")
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env.pop("SENTIMENT_MODELE", None)
        env["PYTHONUTF8"] = "1"
        install = [str(python), "-m", "pip", "install", "--no-cache-dir", "--timeout", "15",
                   "--retries", "0"]
        if args.reuse_dependencies:
            site = subprocess.check_output(
                [str(python), "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
                text=True,
            ).strip()
            Path(site, "local_dependencies.pth").write_text(
                f"import sys; sys.path.append({ascii(sysconfig.get_path('purelib'))})\n",
                encoding="ascii",
            )
            install += ["--no-index", "--no-deps"]
            print("Mode local : dépendances existantes réutilisées.", flush=True)
        subprocess.run([*install, str(wheel)], cwd=outside, env=env, check=True)

        # Les trois paquets doivent provenir de la roue installée dans le nouveau venv.
        subprocess.run([str(python), "-I", "-c", (
            "import sys, api, sentiment_app, ui; from pathlib import Path; "
            "assert all(Path(m.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()) "
            "for m in (api, sentiment_app, ui))"
        )], cwd=outside, env=env, check=True)

        def run(*arguments: str) -> subprocess.CompletedProcess:
            return subprocess.run([str(command), *arguments], cwd=outside, env=env,
                                  capture_output=True, text=True, encoding="utf-8", check=False)

        result = run("--version")
        assert result.returncode == 0 and result.stdout.strip() == f"sentiment-app {version}", result
        result = run("predict", "Très bien")
        assert result.returncode == 1 and "modèle introuvable" in result.stderr, result
        print("Sans SENTIMENT_MODELE : modèle introuvable, code 1.", flush=True)
        env["SENTIMENT_MODELE"] = str(model)
        for text, expected in [
            ("Livraison rapide, produit conforme, très satisfait", "POSITIVE"),
            ("xqzvb wlkptr grombu", "INDETERMINE"),
        ]:
            result = run("predict", text)
            assert result.returncode == 0, result.stderr
            prediction = json.loads(result.stdout)
            assert prediction["label"] == expected, prediction
            print(result.stdout.strip(), flush=True)
    print("Roue installée et exécutée hors du dépôt : OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
