import PySimpleGUI as sg
from psycopg2 import sql
from db_config import get_db_connection

def get_table_structure(table_name, cursor):
    cursor.execute(sql.SQL("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = %s
    """), [table_name])
    
    columns = cursor.fetchall()
    column_names = [col[0] for col in columns]
    column_types = [col[1] for col in columns]
    column_nullable = [col[2] == 'YES' for col in columns]  # 'YES' if the column is nullable
    return column_names, column_types, column_nullable

def convert_value(value, data_type):
    if data_type in ('integer', 'bigint', 'smallint'):
        return int(value)
    elif data_type == 'numeric':
        return float(value)
    elif data_type == 'boolean':
        return value.lower() in ('true', '1', 't', 'y', 'yes')
    elif data_type == 'date':
        from datetime import datetime
        return datetime.strptime(value, '%Y-%m-%d').date()
    elif data_type == 'timestamp':
        from datetime import datetime
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    else:
        return value  # Default to string

def create_crud_window(table_name):
    connection_pool = get_db_connection()
    conn = connection_pool.getconn()
    cursor = conn.cursor()

    # Obter a estrutura da tabela
    column_names, column_types, column_nullable = get_table_structure(table_name, cursor)

    # Remover colunas da lista de colunas, se existirem
    columns_to_remove = ['datacadastro', 'datainscricao', 'dataavaliacao']
    for col in columns_to_remove:
        if col in column_names:
            idx = column_names.index(col)
            column_names.pop(idx)
            column_types.pop(idx)
            column_nullable.pop(idx)

    # Função para ler dados e atualizar a tabela
    def read_data():
        try:
            cursor.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table_name)))
            rows = cursor.fetchall()
            data = [list(row) for row in rows]
            window['table'].update(values=data)
        except Exception as e:
            sg.popup_error(f"Erro ao ler dados da tabela {table_name}:", e)

    # Função para criar um novo registro
    def create_record():
        layout = [
            [sg.Text(col), sg.InputText(key=col)]
            for col in column_names
        ]
        layout.append([sg.Button("Submit"), sg.Button("Cancel")])
        create_window = sg.Window(f"Create {table_name.capitalize()}", layout)
        
        while True:
            event, values = create_window.read()
            if event == sg.WIN_CLOSED or event == "Cancel":
                break
            if event == "Submit":
                # Validação dos campos obrigatórios
                missing_fields = [col for col, nullable in zip(column_names, column_nullable) if not nullable and not values[col]]
                if missing_fields:
                    sg.popup_error(f"Os seguintes campos são obrigatórios e não foram preenchidos: {', '.join(missing_fields)}")
                else:
                    try:
                        # Convertendo valores para os tipos apropriados
                        converted_values = tuple(convert_value(values[col], column_types[idx]) for idx, col in enumerate(column_names))
                        cursor.execute(
                            sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                                sql.Identifier(table_name),
                                sql.SQL(', ').join(map(sql.Identifier, column_names)),
                                sql.SQL(', ').join(sql.Placeholder() * len(column_names))
                            ),
                            converted_values
                        )
                        conn.commit()
                        sg.popup(f"{table_name.capitalize()} criado com sucesso.")
                        read_data()  # Atualizar a tabela após a criação
                        break
                    except Exception as e:
                        sg.popup_error(f"Erro ao criar {table_name}:", e)
        create_window.close()

    # Função para atualizar um registro
    def update_record():
        def load_record():
            record_id = values["record_id"]
            try:
                cursor.execute(
                    sql.SQL("SELECT * FROM {} WHERE {} = %s").format(
                        sql.Identifier(table_name),
                        sql.Identifier(column_names[0])  # Assume que a primeira coluna é o ID
                    ),
                    (record_id,)
                )
                record = cursor.fetchone()
                if record:
                    for idx, col in enumerate(column_names):
                        update_window.Element(col).Update(record[idx])
                else:
                    sg.popup_error(f"Registro com ID {record_id} não encontrado.")
            except Exception as e:
                sg.popup_error(f"Erro ao carregar {table_name}:", e)

        layout = [
            [sg.Text(f"ID do {table_name.capitalize()}"), sg.InputText(key="record_id"), sg.Button("Carregar")]
        ]
        layout.extend([[sg.Text(f"Novo {col}"), sg.InputText(key=col)] for col in column_names])
        layout.append([sg.Button("Submit"), sg.Button("Cancel")])
        update_window = sg.Window(f"Update {table_name.capitalize()}", layout)

        while True:
            event, values = update_window.read()
            if event == sg.WIN_CLOSED or event == "Cancel":
                break
            elif event == "Carregar":
                load_record()
            elif event == "Submit":
                try:
                    set_clause = sql.SQL(', ').join(
                        sql.Composed([sql.Identifier(k), sql.SQL(" = "), sql.Placeholder()]) for k in column_names
                    )
                    # Convertendo valores para os tipos apropriados
                    converted_values = tuple(convert_value(values[col], column_types[idx]) for idx, col in enumerate(column_names))
                    cursor.execute(
                        sql.SQL("UPDATE {} SET {} WHERE {} = %s").format(
                            sql.Identifier(table_name),
                            set_clause,
                            sql.Identifier(column_names[0])  # Assume que a primeira coluna é o ID
                        ),
                        converted_values + (values["record_id"],)
                    )
                    conn.commit()
                    sg.popup(f"{table_name.capitalize()} atualizado com sucesso.")
                    read_data()  # Atualizar a tabela após a atualização
                    break
                except Exception as e:
                    sg.popup_error(f"Erro ao atualizar {table_name}:", e)
                break
        update_window.close()

    # Função para deletar um registro
    def delete_record():
        layout = [
            [sg.Text(f"ID do {table_name.capitalize()}"), sg.InputText(key="record_id")],
            [sg.Button("Submit"), sg.Button("Cancel")]
        ]
        delete_window = sg.Window(f"Delete {table_name.capitalize()}", layout)
        event, values = delete_window.read()
        if event == "Submit":
            try:
                cursor.execute(
                    sql.SQL("DELETE FROM {} WHERE {} = %s").format(
                        sql.Identifier(table_name),
                        sql.Identifier(column_names[0])  # Assume que a primeira coluna é o ID
                    ),
                    (values["record_id"],)
                )
                conn.commit()
                sg.popup(f"{table_name.capitalize()} deletado com sucesso.")
                read_data()  # Atualizar a tabela após a exclusão
            except Exception as e:
                sg.popup_error(f"Erro ao deletar {table_name}:", e)
        delete_window.close()

    # Layout da interface gráfica do CRUD
    layout = [
        #[sg.Text(f"{table_name.capitalize()}")],
        [sg.Button("Criar"), sg.Button("Carregar"), sg.Button("Atualizar"), sg.Button("Apagar")],
        [sg.Table(values=[], headings=column_names, key="table", auto_size_columns=True, display_row_numbers=True, justification='right', num_rows=10, enable_events=True)],
        [sg.Button("Voltar")]
    ]

    window = sg.Window(f"{table_name.capitalize()}", layout)

    # Loop principal do CRUD
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == "Voltar":
            break
        elif event == "Criar":
            create_record()
        elif event == "Carregar":
            read_data()
        elif event == "Atualizar":
            update_record()
        elif event == "Apagar":
            delete_record()

    window.close()
    cursor.close()
    connection_pool.putconn(conn)