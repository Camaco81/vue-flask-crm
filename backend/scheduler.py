# backend/scheduler.py (o integrado en tu app.py)
from flask_apscheduler import APScheduler
from backend.utils.inventory_utils import verificar_tendencia_y_alertar

scheduler = APScheduler()

# Inicializar y programar
if __name__ == '__main__':
    # ... inicializar app Flask
    
    scheduler.init_app(app)
    scheduler.start()

    # Programar la función para que corra todos los días a las 2:00 AM
    scheduler.add_job(
        id='run_seasonal_check',
        func=verificar_tendencia_y_alertar,
        trigger='cron',
        hour=2,
        minute=0
    )
    
    # ...