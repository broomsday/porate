"""
Command-line entry-point to find pores and cavities in PDBs.
"""

from pathlib import Path

import typer
import multiprocessing

from pore import pore, cli, utils, pdb
from pore.constants import VOXEL_SIZE
from pore.paths import ANNOTATED_DF_DIR, ANNOTATED_PDB_DIR


def porate_pdb_id(pdb_id: str) -> None:
    """
    Download the given PDB ID and then porate it.
    """
    if not utils.have_annotation(pdb_id):
        pdb_path = pore.download_pdb_file(pdb_id)
        if pdb_path is None:
            return None

        print(f"Working on: {pdb_id}")
        annotation, annotated_pdb_lines = pore.process_pdb_file(pdb_path)
        annotation_df = utils.make_annotation_dataframe(annotation)

        utils.save_annotation_dataframe(pdb_id, annotation_df)
        print(f"Annotation saved to dataframe as: {(ANNOTATED_DF_DIR / pdb_path.stem).with_suffix('.json')}")
        pdb.save_annotated_pdb(pdb_id, annotated_pdb_lines)
        print(f"Annotation saved to PDB as: {(ANNOTATED_PDB_DIR / pdb_path.stem).with_suffix('.pdb')}")
        print(f"Quick annotation output:")
        print(annotation_df)


def porate_pdb_file(pdb_file: Path) -> None:
    """
    Operate directly on the given PDB file.
    """
    if not utils.have_annotation(pdb_file.stem):
        print(f"Working on: {pdb_file.stem}")
        annotation, annotated_pdb_lines = pore.process_pdb_file(pdb_file)
        annotation_df = utils.make_annotation_dataframe(annotation)

        utils.save_annotation_dataframe(Path(pdb_file).stem, annotation_df)
        print(f"Annotation saved to dataframe as: {(ANNOTATED_DF_DIR / pdb_file.stem).with_suffix('.json')}")
        pdb.save_annotated_pdb(Path(pdb_file).stem, annotated_pdb_lines)
        print(f"Annotation saved to PDB as: {(ANNOTATED_PDB_DIR / pdb_file.stem).with_suffix('.pdb')}")
        print(f"Quick annotation output:")
        print(annotation_df)


def main(
    porate_input: str = typer.Argument(
        ..., help="PDB ID, PDB file, file with one PDB ID per line, or folder containing PDB files"
    ),
    resolution: float = typer.Option(VOXEL_SIZE, help="Edge-length of voxels used to discretize the structure."),
    non_protein: bool = typer.Option(False, help="Include non-protein residues during the calculations."),
    jobs: int = typer.Option(1, help="Number of threads to use."),
):
    """
    Find pores and cavities in the supplied PDB files.
    """

    utils.setup_dirs()
    utils.ensure_protein_components_file()

    utils.set_resolution(resolution)
    utils.set_non_protein(non_protein)
    input_type = cli.guess_input_type(porate_input)

    if input_type == "pdb_id":
        porate_pdb_id(porate_input)
    elif input_type == "pdb_file":
        pdb_file = Path(porate_input)
        porate_pdb_file(pdb_file)
    elif input_type == "id_file":
        with open(porate_input, mode="r", encoding="utf-8") as id_file:
            pdb_ids = [line.strip() for line in id_file.readlines()]
        tasks = [[pdb_id] for pdb_id in pdb_ids]
        with multiprocessing.Pool(processes=jobs) as pool:
            pool.starmap(porate_pdb_id, tasks)
    elif input_type == "pdb_dir":
        pdb_files = Path(porate_input).glob("*.pdb")
        tasks = [[pdb_file] for pdb_file in pdb_files]
        with multiprocessing.Pool(processes=jobs) as pool:
            pool.starmap(porate_pdb_file, tasks)
    else:
        raise RuntimeError("File mode not implemented")


if "__main__" in __name__:
    typer.run(main)
