import os
import pandas as pd
from base import BaseFeature
from encoding_func import target_encoding
from google.cloud import storage
import numpy as np


THREASHOLD = 10

class TargetEncodingThreashold(BaseFeature):
    def import_columns(self):
        return [
            "language",
            "engaged_user_id",
            "engaging_user_id",
            "CASE WHEN reply_engagement_timestamp IS NULL THEN 0 ELSE 1 END AS reply_engagement",
            "CASE WHEN retweet_engagement_timestamp IS NULL THEN 0 ELSE 1 END AS retweet_engagement",
            "CASE WHEN retweet_with_comment_engagement_timestamp IS NULL THEN 0 ELSE 1 END AS retweet_with_comment_engagement",
            "CASE WHEN like_engagement_timestamp IS NULL THEN 0 ELSE 1 END AS like_engagement",
        ]

    def make_features(self, df_train_input, df_test_input):
        df_train_features = pd.DataFrame()
        df_test_features = pd.DataFrame()

        folds_train = self._download_from_gs(
            feather_file_name="StratifiedGroupKFold_training.ftr"
        )

        category_columns = [
            "language",
            "engaged_user_id",
            "engaging_user_id",
        ]

        target_columns = [
            "reply_engagement",
            "retweet_engagement",
            "retweet_with_comment_engagement",
            "like_engagement",
        ]

        for target_col in target_columns:
            print(f'============= {target_col} =============')

            # Get folds
            folds_col = ["StratifiedGroupKFold_retweet_with_comment_engagement"]
            assert len(folds_col) == 1, "The number of fold column must be one"
            folds = folds_train[folds_col]
            n_fold = folds.max().values[0] + 1
            folds_ids = []

            for i in range(n_fold):
                trn_idx = folds[folds != i].dropna().index
                val_idx = folds[folds == i].dropna().index
                folds_ids.append((trn_idx, val_idx))
                print(f"{i+1}fold: n_trn={len(trn_idx)}, n_val={len(val_idx)}")

            for cat_col in category_columns:
                count = df_train_input[cat_col].value_counts()
                unseen_cat_list = count[count < THREASHOLD].index.tolist()
                df_train_input_cp = df_train_input.copy()
                df_train_input_cp.loc[df_train_input_cp[cat_col].isin(unseen_cat_list), target_col] = np.nan
                print(target_col, cat_col, len(count), len(unseen_cat_list))

                train_result, test_result = target_encoding(
                    cat_col, df_train_input_cp, df_test_input, target_col, folds_ids)
                #df_train_input.drop(columns=[f"{cat_col}_ta"], inplace=True)
                #df_test_input.drop(columns=[f"{cat_col}_ta"], inplace=True)
                df_train_features[f"{target_col}__{cat_col}"] = train_result
                df_test_features[f"{target_col}__{cat_col}"] = test_result

        print(df_train_features.isnull().sum())
        print(df_test_features.isnull().sum())
        return df_train_features, df_test_features


if __name__ == "__main__":
    TargetEncodingThreashold.main()
