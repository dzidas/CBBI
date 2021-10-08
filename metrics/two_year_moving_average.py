from typing import List

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from sklearn.linear_model import LinearRegression

from utils import add_common_markers
from .base_metric import BaseMetric


class TwoYearMovingAverageMetric(BaseMetric):
    @property
    def name(self) -> str:
        return '2YMA'

    @property
    def description(self) -> str:
        return '2 Year Moving Average'

    def calculate(self, df: pd.DataFrame, ax: List[plt.Axes]) -> pd.Series:
        df['2YMA'] = df['Price'].rolling(365 * 2).mean()
        df['2YMALog'] = np.log(df['2YMA'])
        df['2YMAx5'] = df['2YMA'] * 5
        df['2YMAx5Log'] = np.log(df['2YMAx5'])

        df['2YMALogDifference'] = df['2YMAx5Log'] - df['2YMALog']
        df['2YMALogOvershootActual'] = df['PriceLog'] - df['2YMAx5Log']
        df['2YMALogUndershootActual'] = df['PriceLog'] - df['2YMALog']

        high_rows = df.loc[(df['PriceHigh'] == 1) & ~ (df['2YMA'].isna())]
        high_x = high_rows.index.values.reshape(-1, 1)
        high_y = high_rows['2YMALogOvershootActual'].values.reshape(-1, 1)

        low_rows = df.loc[(df['PriceLow'] == 1) & ~ (df['2YMA'].isna())]
        low_x = low_rows.index.values.reshape(-1, 1)
        low_y = low_rows['2YMALogUndershootActual'].values.reshape(-1, 1)

        x = df.index.values.reshape(-1, 1)

        lin_model = LinearRegression()
        lin_model.fit(high_x, high_y)
        df['2YMALogOvershootModel'] = lin_model.predict(x)

        lin_model.fit(low_x, low_y)
        df['2YMALogUndershootModel'] = lin_model.predict(x)

        df['2YMAHighModel'] = df['2YMAx5Log'] + df['2YMALogOvershootModel']
        df['2YMALowModel'] = df['2YMALog'] + df['2YMALogUndershootModel']

        df['2YMAIndex'] = (df['PriceLog'] - df['2YMALowModel']) / \
                          (df['2YMAHighModel'] - df['2YMALowModel'])

        df['2YMAIndexNoNa'] = df['2YMAIndex'].fillna(0)
        ax[0].set_title(self.description)
        sns.lineplot(data=df, x='Date', y='2YMAIndexNoNa', ax=ax[0])
        add_common_markers(df, ax[0])

        sns.lineplot(data=df, x='Date', y='PriceLog', ax=ax[1])
        sns.lineplot(data=df, x='Date', y='2YMAHighModel', ax=ax[1])
        sns.lineplot(data=df, x='Date', y='2YMALowModel', ax=ax[1])
        add_common_markers(df, ax[1], price_line=False)

        return df['2YMAIndex']
