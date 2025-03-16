import pandas as pd
import os
# Caso for atualizar uma planilha do Google Sheets, importe também as bibliotecas necessárias
# Ex: import gspread

def main(request=None):
    # URL do arquivo CSV no Tesouro Transparente
    url = "https://www.tesourotransparente.gov.br/ckan/dataset/df56aa42-484a-4a59-8184-7676580c81e3/resource/796d2059-14e9-44e3-80c9-2d9e30b405c1/download/PrecoTaxaTesouroDireto.csv"

    # 1. Lê o arquivo CSV
    df = pd.read_csv(url, sep=';', decimal=',', encoding='latin-1')

    # 2. Converte colunas de data para datetime
    df['Data Base'] = pd.to_datetime(df['Data Base'], format='%d/%m/%Y', errors='coerce')
    df['Data Vencimento'] = pd.to_datetime(df['Data Vencimento'], format='%d/%m/%Y', errors='coerce')

    # 3. Cria a coluna "Titulo" unindo "Tipo Titulo" + "ano" do vencimento
    df['AnoVenc'] = df['Data Vencimento'].dt.year.astype(str)
    df['Titulo'] = df['Tipo Titulo'] + ' ' + df['AnoVenc']

    # 4. Seleciona as colunas de interesse
    df_final = df[[
        'Titulo',
        'Data Base',
        'Taxa Compra Manha',
        'Taxa Venda Manha',
        'PU Base Manha'
    ]].copy()

    df_final.rename(columns={
        'Data Base': 'Data',
        'Taxa Compra Manha': 'TaxaCompra',
        'Taxa Venda Manha': 'TaxaVenda',
        'PU Base Manha': 'PUBase'
    }, inplace=True)

    # 5. Filtra apenas alguns títulos específicos (ajuste conforme sua necessidade)
    df_final = df_final[df_final['Titulo'].isin([
        'Tesouro IPCA+ com Juros Semestrais 2045',
        'Tesouro IPCA+ com Juros Semestrais 2035',
        'Tesouro Prefixado com Juros Semestrais 2035'
    ])]

    # Aqui você implementaria a lógica para atualizar sua planilha do Google Sheets
    # Por exemplo, utilizando a API do Google Sheets ou a biblioteca gspread

    # Opcional: Salva o CSV localmente ou faz upload para algum storage, se necessário
    output_file = '/tmp/dados_filtrados.csv'
    df_final.to_csv(output_file, index=False, encoding='utf-8-sig')
    print("Arquivo 'dados_filtrados.csv' criado com sucesso!")

    # Se for uma Cloud Function HTTP, retorne uma resposta
    if request:
        return "Processamento concluído!", 200

if __name__ == '__main__':
    main()
