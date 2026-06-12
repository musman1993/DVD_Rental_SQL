SELECT 
first_name, 
last_name FROM actor
ORDER BY last_name ASC
;

-- Inventory Check: Find all films that have a rental_rate greater than 4.99 and a rating of 'G'.

-- SELECT * FROM film
-- WHERE rental_rate > 4.99 AND rating = 'G';

-- Goal: Find the email addresses of the first 50 customers in the database (ordered by customer_id).

-- SELECT email FROM customer
-- ORDER BY customer_id LIMIT 50;

-- Goal: List all unique rating types available in the film table.

-- SELECT DISTINCT rating FROM film;

-- Problem #5: Rental Activity
--Goal: Join the customer and rental tables to list the first_name, last_name, and rental_date for every rental.

-- SELECT c.first_name, c.last_name, r.rental_date
-- FROM customer c
-- JOIN rental r ON c.customer_id = r.customer_id;

-- Problem #6: Revenue by Film
-- This is a "Medium-Plus" challenge. To get from a Film Title to the Payment Amount, you have to follow the "breadcrumb trail" in your diagram: film → inventory → rental → payment.

-- SELECT f.title, SUM(p.amount) AS total_revenue
-- FROM film f
-- JOIN inventory i ON f.film_id = i.film_id
-- JOIN rental r    ON i.inventory_id = r.inventory_id
-- JOIN payment p   ON r.rental_id = p.rental_id
-- GROUP BY f.title
-- ORDER BY total_revenue DESC
-- LIMIT 5;

-- Problem #7: Store Performance
-- Let's look at the Physical Inventory side of the business. Look at your diagram and find the store and inventory tables.
-- Goal: Calculate the total number of inventory items held at Store 1 vs. Store 2.

-- SELECT s.store_id, COUNT(i.inventory_id) AS total_inventory
-- FROM store s
-- JOIN inventory i ON s.store_id = i.store_id
-- GROUP BY s.store_id;

-- Problem #8: Popular Categories
-- This is the final challenge of the Medium phase. It introduces a new concept: filtering after you have already grouped the data.
-- Goal: List the categories (e.g., Action, Comedy) and the total number of films in each, but only show categories that have more than 60 films.
-- Tables: category and film_category (Look at the link between them in your diagram).
-- Columns: name (from category), COUNT(film_id).
-- The Trap: You cannot use WHERE to filter the count of 60. You must use the HAVING clause.
-- Tutor Tip: The WHERE clause filters individual rows before they are grouped. The HAVING clause filters the results after they are grouped.

-- SELECT c.name AS category_name, COUNT(fc.film_id) AS total_films
-- FROM category c
-- JOIN film_category fc ON c.category_id = fc.category_id
-- GROUP BY c.name
-- HAVING COUNT(fc.film_id) > 60;

-- Problem #10: Detailed Customer Inventory
-- Goal: List the first name, last name, and email of all customers who live in the city of 'London'.
-- Tables to link: customer → address → city
-- Filter: city.city = 'London'

-- SELECT sum(inventory) as total_inventory_count FROM film;
