# uk_train_time_est
Estimate the arrival time of a route

## Deployment (development server)
- Pull the repo
- Create a virtualenv
- Install dependencies with `pip install -r requirements.txt`
- Provide the transport API **app id** and **app key** via the `TPT_APP_ID` and `TPT_APP_KEY`
environment variables (can use `.env` file) 
- Run the development server with `python main.py`


### API example:
`http://localhost:9000/arrival_time?stations=LBG,SAJ,NWX,BXY&date=2022-09-02&start_time=14:17`
