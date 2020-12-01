import pandas as pd
import numpy as np


def read_data_fyf():
    df = pd.read_csv('./data/f_y_f.csv',
                     sep=',',
                     encoding='utf-8',
                     parse_dates=['Fecha inicio', 'Fecha término'],
                     date_parser=lambda x: pd.to_datetime(x, format="%d-%m-%Y")
                     )

    df.drop(df[df['Fondo inicio'] == 'TOTAL'].index, inplace=True)
    df[['FONDO_1', 'FONDO_2']] = df['Sugerencia FyF'].str.split(pat='/', expand=True)
    df['FONDO_2'].fillna(value=np.nan, inplace=True)

    df[['FONDO_1', 'FONDO_2']] = df['Sugerencia FyF'].str.split(pat='/', expand=True)
    df[['PROP1', 'LETRA_FONDO_1']] = df['FONDO_1'].str.split(pat='%', expand=True)
    df[['PROP2', 'LETRA_FONDO_2']] = df['FONDO_2'].str.split(pat='%', expand=True)

    for col in ['PROP1', 'LETRA_FONDO_1', 'PROP2', 'LETRA_FONDO_2']:
        df[col] = df[col].str.strip()

    for col in ['PROP1', 'PROP2']:
        df[col].fillna(value='0', inplace=True)
        df[col] = df[col].astype('int64')
        df[col] = df[col] / 100

    df['LETRA_FONDO_2'].fillna(value='B', inplace=True)

    # Obtener columnas con fondos
    for letra in ['A', 'B', 'C', 'D', 'E']:
        df['FONDO_COMPRA_' + letra] = 0
        cond1 = df['LETRA_FONDO_1'] == letra
        cond2 = df['LETRA_FONDO_2'] == letra
        df.loc[cond1, 'FONDO_COMPRA_' + letra] = df.loc[cond1, 'PROP1']
        df.loc[cond2, 'FONDO_COMPRA_' + letra] = df.loc[cond2, 'PROP2']

    cols_drop = ['Fecha término', 'Fondo inicio', 'Sugerencia FyF',
                 'FONDO_1', 'FONDO_2', 'PROP1', 'LETRA_FONDO_1', 'PROP2', 'LETRA_FONDO_2']
    df.drop(columns=cols_drop, inplace=True)

    df.sort_values(by=['Fecha inicio'], inplace=True, ignore_index=True)

    return df


def read_data_afp_modelo():
    df = pd.read_csv('./data/valor_cuota_2011_2013.csv',
                     sep=';',
                     encoding='utf-8',
                     parse_dates=['Dia'],
                     date_parser=lambda x: pd.to_datetime(x, format="%d-%m-%Y"),
                     decimal=','
                     )

    for col in ['2014_2016', '2017_2020']:
        df1 = pd.read_csv('./data/valor_cuota_' + col + '.csv',
                          sep=';',
                          encoding='utf-8',
                          parse_dates=['Dia'],
                          date_parser=lambda x: pd.to_datetime(x, format="%d-%m-%Y"),
                          decimal=','
                          )

        df = df.append(df1, ignore_index=True)

    df.sort_values(by=['Dia'], inplace=True, ignore_index=True)

    # Filtrar dias no hábiles
    for letra in ['A', 'B', 'C', 'D', 'E']:
        df['DIFF_' + letra] = df[letra].diff()

    df.drop(df[(df['DIFF_A'] == 0) & (df['DIFF_E'] == 0)].index, inplace=True)
    df.reset_index(drop=True, inplace=True)
    df.drop(columns=['DIFF_A', 'DIFF_B', 'DIFF_C', 'DIFF_D', 'DIFF_E'], inplace=True)

    return df


def numero_cuotas(df, inversion_inicial):
    df_in = df.copy()

    # Variables a calcular
    cuota = {'A': [], 'B': [], 'C': [], 'D': [], 'E': []}
    monto = [inversion_inicial]

    # Parametros
    fondos = ['A', 'B', 'C', 'D', 'E']
    labels_rec = ['FONDO_COMPRA_A', 'FONDO_COMPRA_B', 'FONDO_COMPRA_C', 'FONDO_COMPRA_D', 'FONDO_COMPRA_E']
    periodos = list(range(1, len(df_in)))
    valor_cuota = df_in[fondos].to_dict()
    rec = df_in[labels_rec].to_dict()

    # Cuota inicial
    cuota['A'].append(0)
    cuota['B'].append(0)
    cuota['C'].append(0)
    cuota['D'].append(0)
    cuota['E'].append(inversion_inicial / valor_cuota['E'][0])

    # Cuota i-esima y monto i-esimo
    for periodo in periodos:
        factor_t = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0}
        monto_t = 0
        for fondo in ['A', 'B', 'C', 'D', 'E']:
            factor_t[fondo] = rec['FONDO_COMPRA_' + fondo][periodo] / valor_cuota[fondo][periodo]
            monto_t = cuota[fondo][periodo-1] * valor_cuota[fondo][periodo] + monto_t

        for fondo in ['A', 'B', 'C', 'D', 'E']:
            cuota[fondo].append(factor_t[fondo] * monto_t)
        monto.append(monto_t)

    df_out = pd.DataFrame(cuota)
    df_out['MONTO'] = monto
    return df_out


def main():
    delta = 2
    inversion = 1e6
    fecha = '2011-07-29'

    df1 = read_data_afp_modelo()
    df2 = read_data_fyf()
    df = df1.merge(df2, how='left', left_on='Dia', right_on='Fecha inicio')

    for letra in ['A', 'B', 'C', 'D', 'E']:
        df['FONDO_COMPRA_' + letra] = df['FONDO_COMPRA_' + letra].shift(delta)

    df.drop(df[df['FONDO_COMPRA_A'].isna()].index, inplace=True)
    df.drop(columns=['Fecha inicio'], inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Número de cuotas en un periodo
    cols_cuotas = ['CUOTA_A', 'CUOTA_B', 'CUOTA_C', 'CUOTA_D', 'CUOTA_E']
    df[cols_cuotas + ['MONTO_FyF']] = numero_cuotas(df, 1000000)

    # Crecimiento
    cols_gb = ['A', 'B', 'C', 'D', 'E', 'MONTO_FyF']
    for col in cols_gb:
        df['CREC_' + col] = df[col].pct_change()

    df.to_csv('./data/procesada.csv', sep=';', decimal=',', index=False)


if __name__ == '__main__':

    main()
