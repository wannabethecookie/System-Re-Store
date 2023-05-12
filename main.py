import flask, sqlite3
from flask import render_template, request, url_for

app = flask.Flask(__name__)

carts = []
price = 0

@app.route('/')
def home():
    conn = sqlite3.connect('srs.db')
    cur = conn.execute("SELECT Image, Name, Price, ID FROM Product")
    items = list(cur.fetchall())
    return render_template('home.html', items=items)

@app.route('/info/<prod>/')
def info(prod):
    conn = sqlite3.connect('srs.db')
    cur = conn.execute("SELECT Image, Price, Desc1, Desc2, Desc3, Desc4 FROM Product WHERE ID = ?", (prod,))
    item = list(cur.fetchone())
    return render_template('info.html', item=item, prod=prod)

@app.route('/cart/', methods=['GET','POST'])
def cart():
    global carts
    global price
    if request.method == 'GET':
        price = 0
        for prod in carts:
            price += float(prod[3])
        price = "{:.2f}".format(price)
        return render_template('cart.html', carts=carts, price=price)
    elif request.method == 'POST':
        price = 0
        if ['Add To Cart'] in dict(request.form).values():
            prodNo = int(list(dict(request.form).keys())[-1])
            inCart = False
            conn = sqlite3.connect('srs.db')
            cur = conn.execute("SELECT ID, Name, Image, Price FROM Product WHERE ID = ?", (prodNo,)) 
            item = list(cur.fetchone())
            ogPrice = float(item[3])
            item.append(ogPrice)
            conn.close()
            for prod in carts:
                if item[0] == prod[0]:
                    index = carts.index(prod)
                    inCart = True
                    break
            if inCart == False:
                item.append(1)
                carts.append(item)
            elif inCart == True:
                carts[index][5] += 1
                carts[index][3] = "{:.2f}".format(float(carts[index][3])+ogPrice)
        elif 'Remove' in request.form:
            prodNo = int(request.form.get('Remove'))
            for prod in carts:
                if prod[0] == prodNo:
                    carts.remove(prod)
        elif ['Remove All'] in dict(request.form).values():
            carts = []
        elif 'Update' in request.form: 
            quantities = request.form.getlist("quantity")
            for prod in carts:
                prod[5] = int(quantities[carts.index(prod)])
                prod[3] = "{:.2f}".format(prod[4]*prod[5])
        for prod in carts:
            price += float(prod[3])
        price = "{:.2f}".format(price)
        return render_template('cart.html', carts=carts, price=price)
    
@app.route('/checkout/')
def checkout():
    return render_template('checkout.html')

customerInsert = ()
@app.route('/payment/', methods = ['POST'])
def payment():
    global customerInsert
    global price
    customerInsert = (request.form['fname'], request.form['lname'], request.form['email'], request.form['add1'], request.form['add2'], request.form['country'])
    return render_template('payment.html', price=price)

@app.route('/finish/')
def finish():
    conn = sqlite3.connect('srs.db')
    cur = conn.execute('SELECT EXISTS(SELECT 1 FROM Customer WHERE Email = ?)',(customerInsert[2],))
    rows = cur.fetchone()
    if rows[0] == 0:
        conn.execute('INSERT INTO Customer(FirstName, LastName, Email, Address1, Address2, Country) VALUES (?,?,?,?,?,?)',customerInsert)
        conn.commit()
        cur1 = conn.execute('SELECT seq from sqlite_sequence WHERE name="Customer"')
        cusID = cur1.fetchone()
    elif rows[0] == 1:
        cur1 = conn.execute('SELECT ID FROM Customer WHERE Email = ?',(customerInsert[2],))
        cusID = cur1.fetchone()
        conn.execute('UPDATE Customer Set FirstName=?,LastName=?,Address1=?,Address2=?,Country=? WHERE ID=?',(customerInsert[0],customerInsert[1],customerInsert[3],customerInsert[4],customerInsert[5],cusID[0],))
        conn.commit()
    conn.execute('INSERT INTO Orders(CustomerID) VALUES (?)',(cusID[0],))
    conn.commit()
    cur = conn.execute('SELECT seq from sqlite_sequence WHERE name="Orders"')
    orderID = cur.fetchone()
    for prod in carts:
        conn.execute('INSERT INTO OrderInfo(OrderID, ProductID, Quantity) VALUES (?,?,?)',(orderID[0], prod[0], prod[5]))
    conn.commit()
    conn.close()
    carts.clear()
    return render_template('finish.html', orderID=orderID[0])

if __name__ == '__main__':
    app.run()
