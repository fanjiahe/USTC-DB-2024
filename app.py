from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import base64

# 创建一个Flask实例
app = Flask(__name__)
# 设置数据库名称
DATABASE = "stu1" + ".db"


# 创建数据库表格
def CreateTable_Student():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS T_student (
            student_id INT PRIMARY KEY,
            name VARCHAR(50),
            gender VARCHAR(10),
            grade INT,
            class VARCHAR(10),
            major_code INT,
            status VARCHAR(20),
            password VARCHAR(50)
        );
    """
    )


def InsertData_Student(insert_student):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(insert_student)
    # print("InsertData_Student:", insert_student)
    conn.commit()
    conn.close()


def CreateTable_major():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        """
        -- 创建 T_major 表
        CREATE TABLE IF NOT EXISTS T_major (
            major_code INT PRIMARY KEY,
            major_name VARCHAR(100),
            major_logo BLOB, -- 图片存储使用 BLOB 类型
            people_count INT
        );
    """
    )


def InsertData_major():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    with open("cs.png", "rb") as image_file:
        cs = base64.b64encode(image_file.read()).decode("utf-8")
    with open("ee.png", "rb") as image_file:
        ee = base64.b64encode(image_file.read()).decode("utf-8")
    with open("phy.png", "rb") as image_file:
        phy = base64.b64encode(image_file.read()).decode("utf-8")
    cursor.execute(
        "INSERT INTO T_major (major_code, major_name, major_logo, people_count) VALUES (?, ?, ?, ?);",
        (101, "计科", cs, 2),
    )
    cursor.execute(
        "INSERT INTO T_major (major_code, major_name, major_logo, people_count) VALUES (?, ?, ?, ?);",
        (102, "电子信息", ee, 2),
    )
    cursor.execute(
        "INSERT INTO T_major (major_code, major_name, major_logo, people_count) VALUES (?, ?, ?, ?);",
        (103, "物理", phy, 1),
    )

    conn.commit()
    conn.close()


def CreateTable_course():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        """
        -- 创建 T_course 表
        CREATE TABLE IF NOT EXISTS T_course (
            course_code INT PRIMARY KEY,
            course_name VARCHAR(100)
        );
    """
    )


def InsertData_course(insert_course):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(insert_course)
    print("InsertData_course:", insert_course)
    conn.commit()
    conn.close()


def CreateTable_score():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS T_score (
            score_code INT PRIMARY KEY,
            course_code INT,
            course_name VARCHAR(100),
            student_name VARCHAR(50),
            student_id INT,
            score INT,
            FOREIGN KEY (student_id) REFERENCES T_student(student_id),
            FOREIGN KEY (course_code) REFERENCES T_course(course_code)
        );
    """
    )


def InsertData_score(insert_score):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(insert_score)
    # print("InsertData_score:", insert_score)
    conn.commit()
    conn.close()


def Trigger_update_people_count_when_INSERT_ON_T_student():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        """
            CREATE TRIGGER IF NOT EXISTS before_insert_student
            BEFORE INSERT ON T_student
            FOR EACH ROW
            WHEN NEW.major_code NOT IN (SELECT major_code FROM T_major)
            BEGIN
                INSERT INTO T_major (major_code, major_name, people_count)
                VALUES (NEW.major_code, '', 0);
            END;
    """
    )
    cursor.execute(
        """
            CREATE TRIGGER IF NOT EXISTS after_insert_student
            AFTER INSERT ON T_student
            FOR EACH ROW
            BEGIN
                UPDATE T_major
                SET people_count = people_count + 1
                WHERE major_code = NEW.major_code;
            END;
        """
    )
    conn.commit()
    conn.close()


def Trigger_updete_people_count_when_DELETE_ON_T_student():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TRIGGER IF NOT EXISTS SubtractMajorCount
        AFTER DELETE ON T_student
        BEGIN
        UPDATE T_major
        SET people_count = people_count - 1
        WHERE major_code = OLD.major_code;
        END;
        """
    )
    conn.commit()
    conn.close()


def TRANSACTION_transfer_major(student_id, new_major_code, new_major_name):
    # 检查目标专业（转后专业）是否存在。
    # 如果目标专业不存在，创建新的专业记录。
    # 更新学生记录，将其专业代码更改为新的专业代码。
    # 更新原专业和目标专业的人数计数。

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        # 开始一个事务
        conn.execute("BEGIN TRANSACTION")

        # 更新原专业和目标专业的人数计数
        # 首先获取原专业代码
        cursor.execute(
            "SELECT major_code FROM T_student WHERE student_id = ?", (student_id,)
        )
        old_major_code = cursor.fetchone()[0]
        print("old_major_code:", old_major_code)
        print("new_major_code:", new_major_code)

        # 检查目标专业是否存在
        cursor.execute(
            "SELECT COUNT(*) FROM T_major WHERE major_code = ?", (new_major_code,)
        )
        exists = cursor.fetchone()[0] > 0

        # 如果目标专业不存在，创建新的专业记录
        if not exists:
            cursor.execute(
                "INSERT INTO T_major (major_code, major_name, people_count) VALUES (?, ?, 0)",
                (new_major_code, new_major_name),
            )

        # 更新学生记录，将其专业代码更改为新的专业代码
        cursor.execute(
            "UPDATE T_student SET major_code = ? WHERE student_id = ?",
            (new_major_code, student_id),
        )

        # 原专业人数减一
        cursor.execute(
            "UPDATE T_major SET people_count = people_count - 1 WHERE major_code = ?",
            (old_major_code,),
        )

        # 转后专业人数加一
        cursor.execute(
            "UPDATE T_major SET people_count = people_count + 1 WHERE major_code = ?",
            (new_major_code,),
        )

        # 提交事务
        conn.commit()
    except Exception as e:
        # 如果有任何错误发生，回滚事务
        print("Error:", e)
        conn.rollback()


def data_init():
    CreateTable_Student()
    CreateTable_major()
    CreateTable_course()
    CreateTable_score()
    insert_student_list = [
        """
        -- 插入学生数据
        INSERT INTO T_student (student_id, name, gender, grade, class, major_code, status, password) 
        VALUES 
        (1001, '张三', '女', 1, 'A', 101, '在校', 'pw1'),
        (2001, '李四', '男', 2, 'B', 102, '在校', 'pw2'),
        (3001, '王五', '男', 3, 'C', 103, '离校', 'pw3'),
        (1002, '赵六', '女', 1, 'A', 101, '在校', 'pw4'),
        (2002, '钱七', '男', 2, 'B', 102, '在校', 'pw5');


        """
    ]
    for insert_student in insert_student_list:
        InsertData_Student(insert_student)

    InsertData_major()

    insert_course_list = [
        """
        -- 插入课程数据
        INSERT INTO T_course (course_code, course_name)
        VALUES 
        (201, 'python'),
        (202, '数分'),
        (203, '力学');
    """
    ]
    for insert_course in insert_course_list:
        InsertData_course(insert_course)
    insert_score_list = [
        """
        -- 插入成绩数据
        INSERT INTO T_score (score_code, course_code, course_name, student_name, student_id, score)
        VALUES 
        (301, 201, 'python', '张三', 1001, 85),
        (302, 202, '数分', '李四', 2001, 78),
        (303, 203, '力学', '王五', 3001, 90),
        (304, 202, '数分', '张三', 1001, 86),
        (305, 202, '数分', '赵六', 1002, 88),
        (306, 202, '数分', '钱七', 2002, 76);
        """
    ]
    for insert_score in insert_score_list:
        InsertData_score(insert_score)


# 首页路由
@app.route("/")
def index():
    try:
        data_init()
        print("数据初始化成功")
    except Exception as e:
        # 如果数据库已经存在，就不再初始化数据
        print(e)
        print("数据初始化失败")
    # data_init()
    Trigger_update_people_count_when_INSERT_ON_T_student()
    Trigger_updete_people_count_when_DELETE_ON_T_student()
    return render_template("index.html")


# 显示所有表格
@app.route("/show_table")
def ShowTable():
    # 打印所有表
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM T_student")
    students = cursor.fetchall()
    cursor.execute("SELECT * FROM T_major")
    majors = cursor.fetchall()
    # print(majors)
    cursor.execute("SELECT * FROM T_course")
    courses = cursor.fetchall()
    cursor.execute("SELECT * FROM T_score")
    scores = cursor.fetchall()
    conn.close()
    return render_template(
        "show_table.html",
        students=students,
        majors=majors,
        courses=courses,
        scores=scores,
    )


# 学生登录
@app.route("/login", methods=["POST"])
def login():
    if request.method == "POST":
        student_id = request.form["student_id"]
        password = request.form["password"]
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM T_student WHERE student_id=? AND password=?",
            (student_id, password),
        )
        stu = cursor.fetchall()
        cursor.execute("SELECT * FROM T_score WHERE student_id=?", (student_id,))
        sco = cursor.fetchall()
        print(stu)
        print(sco)
        conn.close()
        if stu:
            return render_template("score.html", student_info=list(stu), score_info=sco)
        else:
            return render_template("fail.html")


# 学生信息处理
@app.route("/update")
def update():
    return render_template("update.html")


# 增加学生信息
@app.route("/add_student", methods=["POST"])
def add():
    if request.method == "POST":
        student_id = request.form["student_id"]
        name = request.form["name"]
        gender = request.form["gender"]
        grade = request.form["grade"]
        class_ = request.form["class"]
        major_code = request.form["major_code"]
        status = request.form["status"]
        password = request.form["password"]
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            """
                INSERT INTO T_student (student_id, name, gender, grade, class, major_code, status, password) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (student_id, name, gender, grade, class_, major_code, status, password),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("ShowTable"))


# 删除学生信息
@app.route("/delete_student", methods=["POST"])
def delete_student():
    if request.method == "POST":
        sid = request.form["student_id"]
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM T_student WHERE student_id=?", (sid,))
        conn.commit()
        conn.close()
        return redirect(url_for("ShowTable"))


# 查询学生信息
@app.route("/search_student", methods=["POST"])
def search_student():
    if request.method == "POST":
        sid = request.form["student_id"]
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM T_student WHERE student_id=?", (sid,))
        stu = cursor.fetchall()
        cursor.execute("SELECT * FROM T_score WHERE student_id=?", (sid,))
        sco = cursor.fetchall()
        conn.close()
        return render_template("score.html", student_info=stu, score_info=sco)


# 修改学生信息
@app.route("/update_student", methods=["POST"])
def update_student():
    if request.method == "POST":
        student_id = request.form["student_id"]
        name = request.form["name"]
        gender = request.form["gender"]
        grade = request.form["grade"]
        class_ = request.form["class"]
        major_code = request.form["major_code"]
        status = request.form["status"]
        password = request.form["password"]
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            "update T_student SET name=?,gender=?,grade=?,class=?,major_code=?,status=?,password=? WHERE student_id=? ",
            (name, gender, grade, class_, major_code, status, password, student_id),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("ShowTable"))


# 按性别查找学生
@app.route("/get_boy_or_girl", methods=["POST"])
def Procedure_getBorG():
    if request.method == "POST":
        gen = request.form["gender"]
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    if gen == "女":
        cursor.execute("DROP VIEW IF EXISTS female_students;")

        cursor.execute(
            """
            CREATE VIEW female_students AS
            SELECT *
            FROM T_student
            WHERE gender ='女';
            """
        )
        cursor.execute("SELECT * FROM female_students")
        res_BorG = cursor.fetchall()
    else:
        cursor.execute("DROP VIEW IF EXISTS male_students;")

        cursor.execute(
            """
            CREATE VIEW male_students AS
            SELECT *
            FROM T_student
            WHERE gender ='男';
            """
        )
        cursor.execute("SELECT * FROM male_students")
        res_BorG = cursor.fetchall()

    conn.commit()
    conn.close()
    return render_template("show_table.html", students=res_BorG)

# 按专业查找学生
@app.route("/get_student_by_major", methods=["POST"])
def Procedure_get_student_by_major():
    if request.method == "POST":
        major_code = request.form["major_code"]
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM T_student WHERE major_code=?", (major_code,))
    # cursor.execute(
    #     """
    #     create PROCEDURE get_student_by_major(major_code INT)
    #     begin
    #         select * from T_student where major_code = major_code;
    #     end;
    #     """
    # )
    # cursor.execute("CALL get_student_by_major(%s)" % major_code)

    # # SQLite不支持存储过程（PROCEDURE）和函数（FUNCTION）的创建
    # # 这是它与传统的关系型数据库管理系统（如MySQL、PostgreSQL、Oracle）的一个主要区别
    # # 在SQLite中，不能创建或调用存储过程。

    res = cursor.fetchall()
    conn.close()
    return render_template("show_table.html", students=res)

# 修改专业
@app.route("/change_major", methods=["POST"])
def Transaction_change_major():
    if request.method == "POST":
        student_id = request.form["student_id"]
        major_code = request.form["major_code"]
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    TRANSACTION_transfer_major(student_id, major_code, "新专业")
    conn.commit()
    conn.close()
    return redirect(url_for("ShowTable"))


if __name__ == "__main__":
    app.run(debug=True)
