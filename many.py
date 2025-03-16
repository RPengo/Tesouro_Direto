from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

@app.route("/", methods=["GET"])
def process_data():
    # URL do arquivo CSV no Tesouro Transparente
    url = "https://www.tesourotransparente.gov.br/ckan/dataset/df56aa42-484a-4a59-8184-7676580c81e3/resource/796d2059-14e9-44e3-80c9-2d9e30b405c1/download/PrecoTaxaTesouroDireto.csv"

    try:
        # 1. Lê o arquivo CSV
        df = pd.read_csv(url, sep=';', decimal=',', encoding='latin-1')
    except Exception as e:
        return jsonify({'error': f'Erro ao ler o CSV: {str(e)}'}), 500

    try:
        # 2. Converte colunas de data para datetime
        df['Data Base'] = pd.to_datetime(df['Data Base'], format='%d/%m/%Y', errors='coerce')
        df['Data Vencimento'] = pd.to_datetime(df['Data Vencimento'], format='%d/%m/%Y', errors='coerce')

        # 3. Cria a coluna "Titulo" unindo "Tipo Titulo" + "AnoVenc"
        df['AnoVenc'] = df['Data Vencimento'].dt.year.astype(str)
        df['Titulo'] = df['Tipo Titulo'] + ' ' + df['AnoVenc']

        # 4. Seleciona apenas as colunas necessárias: Titulo, Data Base e PU Base Manhã
        df_final = df[['Titulo', 'Data Base', 'PU Base Manha']].copy()

        # 5. Renomeia as colunas para facilitar a leitura
        df_final.rename(columns={
            'Data Base': 'Data',
            'PU Base Manha': 'PUBase'
        }, inplace=True)

        # Opcional: Salva o CSV localmente (em ambiente Cloud Run, use /tmp)
        output_file = '/tmp/dados_filtrados.csv'
        df_final.to_csv(output_file, index=False, encoding='utf-8-sig')
    except Exception as e:
        return jsonify({'error': f'Erro durante o processamento: {str(e)}'}), 500

    # Aqui, futuramente, você poderá implementar a lógica de atualização do Google Sheets.
    # Por enquanto, retornamos uma mensagem de sucesso e os dados processados.
    return jsonify({
        'message': "Arquivo 'dados_filtrados.csv' criado com sucesso!",
        'data': df_final.to_dict(orient='records')
    }), 200

if __name__ == '__main__':
    # Cloud Run exige que a aplicação escute na porta 8080
    app.run(host='0.0.0.0', port=8080)
