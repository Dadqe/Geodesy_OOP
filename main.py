from fastapi import FastAPI
import calc

app = FastAPI(title="Геодезия")

db = calc.DB()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/nums_initial_data")
async def nums_initial_data():
    return {"nums": db.get_count_initial_data()}

@app.get("/Test_data{num}")
async def Test_data(num):
    db.take_data(int(num))
    p = calc.Polygon(db.get_all_data())
    
    return p.return_calculated_data()


# Для 4ки и остальных надо придумать обработчик ошибок, вот на бэке то есть ошибка а на фронт ничего не уходит, видимо, где-то except писать надо.