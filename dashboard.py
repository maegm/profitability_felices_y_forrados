import plotly.express as px
import pandas as pd
import datapane as dp

df = pd.read_csv('./data/procesada.csv',
                 sep=';',
                 encoding='utf-8',
                 parse_dates=['Dia'],
                 date_parser=lambda x: pd.to_datetime(x, format="%Y-%m-%d")
                 )

cols_plot = ['CREC_A', 'CREC_B', 'CREC_C', 'CREC_D', 'CREC_E', 'CREC_MONTO_FyF']
fig = px.line(df, x='Dia', y=cols_plot, title='Crecimiento según fondo')
fig.update_xaxes(rangeslider_visible=True)
# fig.show()

# Once you have the df and the chart, simply use
r = dp.Report(
  dp.Markdown('Crecimiento Felices y Forrados'), #add description to the report
  dp.Plot(fig) #create a chart
)

# Publish your report. Make sure to have visibility='PUBLIC' if you want to share your report
r.publish(name='Crecimiento Felices y Forrados', visibility='PUBLIC')
