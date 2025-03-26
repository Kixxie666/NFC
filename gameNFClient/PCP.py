import mysql.connector

def send_score_to_mysql(user_name, score):
    db_name = "GameShow"
    username = "Admin"
    password = "qwerty"
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user=username,
            password=password,
            database=db_name
        )

        mycursor = mydb.cursor()

        sql_create_users_table = """
            CREATE TABLE IF NOT EXISTS USERS (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE
            )
        """
        mycursor.execute(sql_create_users_table)
        mydb.commit()

        sql_create_scores_table = """
            CREATE TABLE IF NOT EXISTS SCORE (
                score_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                score INT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES USERS(user_id)
            )
        """
        mycursor.execute(sql_create_scores_table)
        mydb.commit()

        sql_select_user = "SELECT user_id FROM USERS WHERE username = %s"
        mycursor.execute(sql_select_user, (user_name,))
        user_id = mycursor.fetchone()

        if user_id:
            sql_select_score = "SELECT score_id FROM SCORE WHERE user_id = %s"
            mycursor.execute(sql_select_score, (user_id[0],))
            score_id = mycursor.fetchone()

            if score_id:
                sql_update_score = "UPDATE SCORE SET score = %s WHERE score_id = %s"
                mycursor.execute(sql_update_score, (score, score_id[0]))
                mydb.commit()
                print("Score updated in MySQL database successfully!")
            else:
                sql_insert_score = "INSERT INTO SCORE (user_id, score) VALUES (%s, %s)"
                mycursor.execute(sql_insert_score, (user_id[0], score))
                mydb.commit()
                print("Score sent to MySQL database successfully!")
        else:
            sql_insert_user = "INSERT INTO USERS (username) VALUES (%s)"
            mycursor.execute(sql_insert_user, (user_name,))
            mydb.commit()

            user_id = mycursor.lastrowid

            sql_insert_score = "INSERT INTO SCORE (user_id, score) VALUES (%s, %s)"
            mycursor.execute(sql_insert_score, (user_id, score))
            mydb.commit()
            print("User and score sent to MySQL database successfully!")

    except mysql.connector.Error as err:
        print("Error sending score to MySQL database:", err)

    finally:
        if mydb.is_connected():
            mydb.close()
            print("MySQL connection closed")

