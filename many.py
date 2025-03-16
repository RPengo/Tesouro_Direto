from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json
import os

app = Flask(__name__)

@app.route("/", methods=["GET"])
def update_spreadsheet():
    try:
        # Carrega as credenciais do ambiente (variável GOOGLE_CREDENTIALS com o JSON das credenciais)
        json_creds = os.environ.get("GOOGLE_CREDENTIALS")
        if not json_creds:
            return jsonify({"error": "Credenciais não encontradas. Configure a variável de ambiente GOOGLE_CREDENTIALS."}), 500
        
        creds_dict = json.loads(json_creds)
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # Abre a planilha e a aba específicas
        spreadsheet = client.open('Dados Tesouro')  # Nome da planilha
        worksheet = spreadsheet.worksheet('Cotações')  # Nome da aba

        # URL do CSV do Tesouro Transparente
        url = (
            "https://www.tesourotransparente.gov.br/ckan/dataset/"
            "df56aa42-484a-4a59-8184-7676580c81e3/resource/"
            "796d2059-14e9-44e3-80c9-2d9e30b405c1/download/PrecoTaxaTesouroDireto.csv"
        )
        
        # Lê o CSV
        df = pd.read_csv(url, sep=';', decimal=',', encoding='latin-1')

        # Processa as datas e cria a coluna 'Titulo'
        df['Data Base'] = pd.to_datetime(df['Data Base'], format='%d/%m/%Y', errors='coerce')
        df['Data Vencimento'] = pd.to_datetime(df['Data Vencimento'], format='%d/%m/%Y', errors='coerce')
        df['AnoVenc'] = df['Data Vencimento'].dt.year.astype(str)
        df['Titulo'] = df['Tipo Titulo'] + ' ' + df['AnoVenc']

        # Seleciona as colunas desejadas
        df_subset = df[['Titulo', 'Data Base', 'PU Base Manha']].copy()
        # Remove linhas sem data para evitar problemas no agrupamento
        df_subset = df_subset.dropna(subset=['Data Base'])
        
        # Para cada 'Titulo', seleciona a linha com a data mais recente
        df_grouped = df_subset.loc[df_subset.groupby('Titulo')['Data Base'].idxmax()].reset_index(drop=True)
        
        # Formata a data para string
        df_grouped['Data'] = df_grouped['Data Base'].dt.strftime('%d/%m/%Y')
        
        # Seleciona e renomeia as colunas para a planilha
        df_final = df_grouped[['Titulo', 'Data', 'PU Base Manha']].copy()
        df_final.rename(columns={'PU Base Manha': 'PUBase'}, inplace=True)

        # Prepara os dados para a planilha (incluindo cabeçalho)
        data_to_update = [df_final.columns.tolist()] + df_final.values.tolist()

        # Limpa a aba antes de atualizar
        worksheet.clear()

        # Atualiza a planilha; se ocorrer uma exceção "<Response [200]>", trata como sucesso
        try:
            worksheet.update('A1', data_to_update)
        except Exception as ex:
            if "<Response [200]>" in str(ex):
                pass
            else:
                raise ex

        return jsonify({"message": "Planilha atualizada com sucesso!", "rows": len(df_final)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
