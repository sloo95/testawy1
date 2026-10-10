from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# إعدادات قاعدة بيانات SQLite
DATABASE_URL = "sqlite:///./notes.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# تعريف جدول الملاحظات في قاعدة البيانات
class NoteDB(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)

# إنشاء الجداول تلقائياً
Base.metadata.create_all(bind=engine)

app = FastAPI()


# تفعيل الـ CORS ليعمل بسلاسة مع المتصفح والتطبيق
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NoteCreate(BaseModel):
    title: str
    content: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"message": "سيرفر ملاحظات NoteOk مدعوم بقاعدة بيانات SQLite شغال 100%!"}

# جلب الملاحظات
@app.get("/notes")
def get_notes(db: Session = Depends(get_db)):
    notes = db.query(NoteDB).all()
    return {"notes": notes}

# إضافة ملاحظة جديدة
@app.post("/notes")
def add_note(note: NoteCreate, db: Session = Depends(get_db)):
    new_note = NoteDB(title=note.title, content=note.content)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return {"message": "تم حفظ الملاحظة في قاعدة البيانات بنجاح!", "note": new_note}

# حذف ملاحظة بواسطة الـ ID
@app.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(NoteDB).filter(NoteDB.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="الملاحظة غير موجودة!")
    
    db.delete(note)
    db.commit()
    return {"message": "تم حذف الملاحظة بنجاح!"}

# تعديل ملاحظة سابقة
@app.put("/notes/{note_id}")
def update_note(note_id: int, note_data: NoteCreate, db: Session = Depends(get_db)):
    note = db.query(NoteDB).filter(NoteDB.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="الملاحظة غير موجودة!")
    
    note.title = note_data.title
    note.content = note_data.content
    db.commit()
    db.refresh(note)
    return {"message": "تم تعديل الملاحظة بنجاح!", "note": note}