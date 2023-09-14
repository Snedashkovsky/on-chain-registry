import pandas as pd

from config import CSV_FILE_PATH


def save_to_csv(
        assets_df: pd.DataFrame,
        file_path: str = CSV_FILE_PATH) -> None:
    """
    Save an assets metadata dataframe to a csv file
    :param assets_df: an assets metadata dataframe
    :param file_path: csv file path
    :return: none
    """
    assets_df.to_csv(file_path)
