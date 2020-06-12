import os
import numpy as np
import pandas as pd
from base import BaseFeature
from google.cloud import storage
from utils import download_from_gcs
from io import BytesIO


class MetaFeatures2ndModels(BaseFeature):
    def import_columns(self):
        return [
            "1"
        ]

    def make_features(self, df_train_input, df_test_input):
        df_train_features = pd.DataFrame()
        df_test_features = pd.DataFrame()

        model_1 = "2nd_stage_model_1_lr0.01_models5_data1000000"
        model_2 = "2nd_stage_model_1_lr0.01_models5_data100000"

        target_columns = {
                "reply_engagement": model_1,
                "retweet_engagement": model_1,
                "retweet_with_comment_engagement": model_1,
                "like_engagement": model_2,
        }

        for target_col, model in target_columns.items():
            print(f'============= {target_col} =============')

            oof_file_name = f"{target_col}_oof_pred.npy"
            oof_pred = download_from_gcs(
                bucket_dir_name=f"model_lgb_hakubishin_20200317/{model}",
                file_name=oof_file_name
            )
            oof_pred_value = np.load(BytesIO(oof_pred))
            df_train_features[target_col] = oof_pred_value

            if self.TESTING:
                test_file_name = f"{target_col}_submission_test.csv"
            else:
                test_file_name = f"{target_col}_submission_val_20200418.csv"
            test_pred = download_from_gcs(
                bucket_dir_name=f"model_lgb_hakubishin_20200317/{model}",
                file_name=test_file_name
            )
            test_pred = pd.read_csv(BytesIO(test_pred), header=None)
            test_pred_value = test_pred.iloc[:, 2].values
            df_test_features[target_col] = test_pred_value

        print(df_train_features.shape)
        print(df_test_features.shape)
        print(df_train_features.isnull().sum())
        print(df_test_features.isnull().sum())

        return df_train_features, df_test_features


if __name__ == "__main__":
    MetaFeatures.main()
