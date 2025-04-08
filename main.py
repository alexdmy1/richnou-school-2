import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

# Données
df_scores = pd.read_csv("fr-en-indicateurs-de-resultat-des-lycees-gt_v2.csv", sep=";", low_memory=False)
df_annuaire = pd.read_csv("fr-en-annuaire-education.csv", sep=";", low_memory=False)

df = pd.merge(df_scores, df_annuaire, left_on="UAI", right_on="Identifiant_de_l_etablissement")
df = df[(df["Region"] == "ILE-DE-FRANCE") & (df["Type_etablissement"] == "Lycée")]

# Options filtres
def creer_options(colonne):
    return [{"label": v, "value": v} for v in sorted(df[colonne].dropna().unique())]

options_dept = creer_options("Libelle_departement")
options_ville = creer_options("Nom_commune")
options_etab = creer_options("Nom_etablissement")
options_annee = [{"label": str(a), "value": a} for a in sorted(df["Annee"].dropna().unique())]
liste_series = ['Toutes series', 'L', 'ES', 'S', 'Gnle', 'STI2D', 'STD2A', 'STMG', 'STL', 'ST2S', 'S2TMD', 'STHR']

# App Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout
def dropdown_filtre(id_, label, options):
    return html.Div([html.Label(label), dcc.Dropdown(id=id_, options=options)])

zone_filtres = html.Div([
    html.H4("Filtres"),
    dropdown_filtre("filtre-dept", "Département", options_dept),
    dropdown_filtre("filtre-ville", "Commune", options_ville),
    dropdown_filtre("filtre-etab", "Établissement", options_etab),
    dropdown_filtre("filtre-spec", "Spécialité", [{"label": s, "value": s} for s in liste_series]),
    dropdown_filtre("filtre-annee", "Année", options_annee)
], style={"padding": "20px"})

zone_contenu = html.Div([
    dcc.Graph(id="graphe-carte"),
    dcc.Graph(id="graphe-barres")
], style={"padding": "20px"})

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(zone_filtres, width=3, className="bg-light"),
        dbc.Col(zone_contenu, width=9)
    ], style={"height": "100vh"})
], fluid=True)

# Callback
@app.callback(
    [Output("graphe-carte", "figure"), Output("graphe-barres", "figure")],
    [Input("filtre-dept", "value"),
     Input("filtre-ville", "value"),
     Input("filtre-etab", "value"),
     Input("filtre-spec", "value"),
     Input("filtre-annee", "value")]
)
def maj_graphs(dept, ville, etab, spec, annee):
    d = df.copy()

    filtres = {
        "Libelle_departement": dept,
        "Nom_commune": ville,
        "Nom_etablissement": etab,
        "Annee": annee
    }

    for col, val in filtres.items():
        if val:
            d = d[d[col] == val]

    if spec:
        col_spec = f"Taux de reussite - {spec}"
        if col_spec in d.columns:
            d = d[d[col_spec] > 0]

    # Graphe carte
    carte = px.scatter_mapbox(
        d, lat="latitude", lon="longitude", zoom=10,
        hover_name="Nom_etablissement",
        color="Taux de reussite - Toutes series",
        mapbox_style="carto-positron"
    )

    if not d.empty:
        carte.update_layout(mapbox_center={"lat": d["latitude"].mean(), "lon": d["longitude"].mean()})

    # Graphe barres
    if etab and not d.empty:
        row = d.drop_duplicates(subset='Annee').iloc[0]
        taux = [row.get(f"Taux de reussite - {serie}", 0) for serie in liste_series]
        barres = px.bar(
            pd.DataFrame({"Série": liste_series, "Taux": taux}),
            x="Série", y="Taux", text="Taux",
            title=f"Réussite - {etab} ({annee or 'Toutes années'})"
        )
        barres.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
        barres.update_layout(yaxis_range=[0, 100])
    else:
        barres = px.bar(title="Veuillez sélectionner un établissement")

    return carte, barres

# Run
if __name__ == "__main__":
    app.run(debug=True)