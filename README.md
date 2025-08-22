<h1 align="center"> Order Processing Application </h1>

<p align="center">
  <img src="assets/cheese_orders_bot.jpeg" width="200">
</p>


## Stack
![Python](https://img.shields.io/badge/-Python-1d1717?style=for-the-badge&logo=Python&logoColor=fff6f6)
![Aiogram](https://img.shields.io/badge/-Aiogram-1d1717?style=for-the-badge&logo=Aiogram&logoColor=fff6f6)
![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-1d1717?style=for-the-badge&logo=PostgreSQL&logoColor=fff6f6)
![SQLAlchemy](https://img.shields.io/badge/-SQLAlchemy-1d1717?style=for-the-badge&logo=SQLAlchemy&logoColor=fff6f6)
![Redis](https://img.shields.io/badge/-Redis-1d1717?style=for-the-badge&logo=Redis&logoColor=fff6f6)
![Docker](https://img.shields.io/badge/-Docker-1d1717?style=for-the-badge&logo=Docker&logoColor=fff6f6)
![Alembic](https://img.shields.io/badge/-Alembic-1d1717?style=for-the-badge&logo=Alembic&logoColor=fff6f6)

## Description

A chat bot for processing customer orders in the artisanal cheese production business. The application allows managing products, creating orders, controlling their processing stages, and collecting data for sales analysis. The product database is shared with [the inventory management application for retail outlets](https://github.com/AleIgoKha/outlets_inventory_bot).  

A key feature of the bot is its interface: all interaction happens within a single pinned message, which makes it feel like a full-fledged application rather than a typical chat bot.

## Project Goals

- Improve the user experience at all stages of order processing  
- Reduce the time required to handle orders  
- Minimize errors in price calculation  
- Collect and store sales data for further analysis  

## How It Works 

Main entities: product, session and order.
<p align="left">
  <img src="assets/main_menu.png" width="400">
</p>

- **Product** — represents an item with a price and unit of measurement.
<p align="left">
  <img src="assets/product_menu.png" width="400">
</p>

- **Session** — groups orders with common parameters (e.g., date, location, event).
<p align="left">
  <img src="assets/session_menu.png" width="400">
</p>

- **Order** — includes selected products and options (packaging, delivery, discounts, etc.).
<p align="left">
  <img src="assets/order_menu.png" width="400">
</p>


Order lifecycle:  

1. **Processing** — record the actual weight of each product and verify the order is correctly assembled.
<p align="left">
  <img src="assets/processing_menu.png" width="400">
</p>

1. **Completed** — the order is fully completed and ready for delivery.
<p align="left">
  <img src="assets/completed_order.png" width="400">
</p>

1. **Issued** — the order has been handed over to the customer.
<p align="left">
  <img src="assets/issued_menu.png" width="400">
</p>

All order parameters can be updated at any stage.
<p align="left">
  <img src="assets/order_changing_1.png" width="400">
  <img src="assets/order_changing_2.png" width="400">
</p>