# sudo pip3 install flask
from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error


# create a server process
app = Flask(__name__)


def open_connection():
  """
  Open MySQL connection with error handling
  """
  try:
    connection = mysql.connector.connect(
      host="localhost",
      user="root",
      password="Pass@7020",
      database="crop_selector"
    )
    return connection
  except Error as e:
    print(f"Error connecting to MySQL: {e}")
    return None


def execute_select_query(query, params=None):
  """
  Execute SELECT query and return output with error handling
  """
  connection = open_connection()
  if not connection:
    return None, "Database connection failed"
  try:
    cursor = connection.cursor()
    cursor.execute(query, params or ())
    data = cursor.fetchall()
    cursor.close()
    connection.close()
    return data, None
  except Error as e:
    print(f"Error executing SELECT query: {e}")
    if cursor:
      cursor.close()
    if connection:
      connection.close()
    return None, str(e)


def execute_query(query, params=None):
  """
  Execute INSERT, UPDATE, DELETE queries with error handling
  """
  connection = open_connection()
  if not connection:
    return "Database connection failed"
  try:
    cursor = connection.cursor()
    cursor.execute(query, params or ())
    connection.commit()
    cursor.close()
    connection.close()
    return None
  except Error as e:
    print(f"Error executing query: {e}")
    if cursor:
      cursor.close()
    if connection:
      connection.close()
    return str(e)


def create_response(data=None, error=None):
    """
    Create a robust response structure
    """
    result = {}
    if error is None:
        result['status'] = 'success'
        result['data'] = data
    else:
        result['status'] = 'error'
        result['error'] = error
        result['data'] = None
    return jsonify(result)


@app.route("/", methods=["GET"])
def welcome():
  return "welcome to my IoT application"


@app.route("/sensordata", methods=["GET"])
def get_sensordata():
    query = "SELECT id, temperature, humidity, moisture, rain, read_time FROM sensordata ORDER BY id DESC LIMIT 10"
    sensordata, error = execute_select_query(query)
    if error:
        return create_response(error=error)

    sensor_values = []
    for (id, temperature, humidity, moisture, rain, read_time) in sensordata:
        sensor_values.append({
            "id": id,
            "temperature": temperature,
            "humidity": humidity,
            "moisture": moisture,
            "rain": rain,
            "read_time": str(read_time)
        })
    return create_response(data=sensor_values)


@app.route('/add-sensordata', methods=["POST"])
def post_sensordata():
  # Validate input
  data = request.get_json(force=True)
  required_fields = ["temperature", "humidity", "moisture", "rain"]
  missing = [field for field in required_fields if field not in data]
  if missing:
    return create_response(error=f"Missing fields: {', '.join(missing)}")

  try:
    temperature = float(data["temperature"])
    humidity = float(data["humidity"])
    moisture = float(data["moisture"])
    rain = float(data["rain"])
  except (ValueError, TypeError) as e:
    return create_response(error=f"Invalid input types: {e}")

  query = "INSERT INTO sensordata (temperature, humidity, moisture, rain) VALUES (%s, %s, %s, %s)"
  error = execute_query(query, (temperature, humidity, moisture, rain))
  if error:
    return create_response(error=error)

  return create_response(data="Added temperature, humidity, moisture, and rain")


# start the server
if __name__ == "__main__":
  app.run(host="0.0.0.0", debug=True, port=4000)

