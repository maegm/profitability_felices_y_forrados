import plotly.express as px
import pandas as pd
import datapane as dp


def variaciones_anuales(df):
    df2 = df.copy()
    df2['AÑO'] = df2['Fecha'].dt.year
    df2['MES'] = df2['Fecha'].dt.month
    df2['DIA'] = df2['Fecha'].dt.day

    df2.drop(df2[df2['MES'] != 1].index, inplace=True)
    df2.sort_values(by=['AÑO', 'MES', 'DIA'], inplace=True, ignore_index=True)
    df2.drop_duplicates(subset=['AÑO', 'MES'], inplace=True, ignore_index=True)

    for fondo in ['A', 'B', 'C', 'D', 'E']:
        df2['VAR_' + fondo] = df2['FONDO_' + fondo].pct_change() * 100
        df2['VAR_' + fondo] = df2['VAR_' + fondo].round(1)
    df2['VAR_FyF'] = df2['FyF'].pct_change() * 100
    df2['VAR_FyF'] = df2['VAR_FyF'].round(1)

    df2.drop(columns=['Fecha', 'CUOTA_A', 'CUOTA_B', 'CUOTA_C', 'CUOTA_D', 'CUOTA_E', 'FyF',
                      'FONDO_A', 'FONDO_B', 'FONDO_C', 'FONDO_D', 'FONDO_E', 'MES', 'DIA'], inplace=True)

    for anio in [2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020]:
        df2.loc[df2['AÑO'] == anio, 'AÑO'] = str(anio) + '/' + str(anio - 1)

    df2.rename(columns={'AÑO': 'Variacion anual'}, inplace=True)
    df2.drop(df2[df2['VAR_A'].isna()].index, inplace=True)
    df2.reset_index(drop=True, inplace=True)
    df2.style.applymap(highlight_max)

    return df2


def file_markdown(filename):

    # Open and read the file as a single buffer
    fd = open('./texto/' + filename, 'r', encoding='utf-8')
    md_file = fd.read()
    fd.close()

    return md_file


def highlight_max(cell):
    """
    Define a function for colouring negative values red and positive values black
    :param cell:
    :return:
    """
    if type(cell) != str and cell < 0 :
        return 'color: red'
    else:
        return 'color: black'


def main():
    df = pd.read_csv('./data/evolucion_temporal.csv',
                     sep=';',
                     encoding='utf-8',
                     parse_dates=['Dia'],
                     date_parser=lambda x: pd.to_datetime(x, format="%Y-%m-%d")
                     )

    df.rename(columns={'Dia': 'Fecha'}, inplace=True)
    cols_plot = ['FONDO_A', 'FONDO_B', 'FONDO_C', 'FONDO_D', 'FONDO_E', 'FyF']
    fig = px.line(df, x='Fecha', y=cols_plot, title='Evolución fondos')
    fig.update_xaxes(rangeslider_visible=True)
    # fig.write_html("./data/evolucion_historica.html", auto_open=True)

    # Reporte
    r = dp.Report(
        dp.Markdown(file_markdown('intro.md')),
        dp.Table(variaciones_anuales(df)),
        dp.Markdown(file_markdown('evolucion.md')),
        dp.Plot(fig),
        dp.Markdown(file_markdown('conclusiones.md')),
    )

    # Publish your report. Make sure to have visibility='PUBLIC' if you want to share your report
    r.publish(name='Crecimiento Felices y Forrados', visibility='PUBLIC')


if __name__ == '__main__':
    main()
