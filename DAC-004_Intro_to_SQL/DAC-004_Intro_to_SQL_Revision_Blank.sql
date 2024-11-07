-- Tutorial: Getting used to SQL is a very important step in landing a job or an internship in tech! 
-- Lets practise using adventureworks

-- Be sure to keep praticising!
-- Here are some questions to practise your skill using the Adventureworks db.

-------------------------------------------------------------------------------------------------------------------------------------------

-- Q1: From the following table humanresources.employee write a query in SQL to retrieve all the rows and columns from the employee table in the Adventureworks database. 
-- Sort the result set in ascending order on jobtitle.
-- humanresources.employee table

--Answer 
SELECT * FROM humanresources.employee
ORDER BY jobtitle asc;

-------------------------------------------------------------------------------------------------------------------------------------------

-- Q2: From the following table person.person write a query in SQL to return all rows and a subset of the columns (firstName, lastName, businessentityid) from the person table in the AdventureWorks database. 
-- The third column heading is renamed to employee_id. Arranged the output in ascending order by lastname.

--Answer

SELECT firstname,lastname,businessentityid as employee_id FROM person.person
ORDER BY lastname asc;
-------------------------------------------------------------------------------------------------------------------------------------------

-- Q3: From the following table write a query in SQL to return only the rows for product that have a sellstartdate that is not NULL and a productline of 'T'. 
-- Return productid, productnumber, and name. Change the name to productname. Arranged the output in ascending order on name.

-- production.product

--Answer

select*from production.product

Select productid, productnumber, name as productname
FROM production.product
WHERE sellstartdate IS NOT NULL 
AND productline = 'T'
ORDER BY productname;
-------------------------------------------------------------------------------------------------------------------------------------------

-- Q4:From the following table write a query in SQL to calculate the total freight paid by each customer. Return customerid and total freight. 
-- Sort the output in ascending order on customerid

-- sales.salesorderheader

--Answer
SELECT customerid, sum(freight) as totalfreight 
FROM sales.salesorderheader
GROUP BY customerid


-------------------------------------------------------------------------------------------------------------------------------------------

-- Q5:From the following table write a query in SQL to retrieve the number of employees for each City. Return city and number of employees. 
-- Sort the result in ascending order on city.

-- person.businessentityaddress

--Answer
Select * from person.businessentityaddress

SELECT * FROM person.address

SELECT a.city as city, COUNT(*) as numberofemployee FROM person.businessentityaddress b
LEFT JOIN person.address a on a.addressid = b.addressid
GROUP BY city
ORDER BY city asc;


------------------------------------------------------------------------------------------------------------------------------------------

-- Q6: From the following tables write a query in SQL to make a list of contacts who are designated as 'Purchasing Manager'. 
-- Return BusinessEntityID, LastName, and FirstName columns. Sort the result set in ascending order of LastName, and FirstName.

-- person.businessentitycontact, person.contacttype, person.person

--Answer
select * from person.businessentitycontact
select * from person.contacttype
select * from person.person

SELECT b.businessentityid as BusinessEntityID, 
p.lastname as LastName,
p.firstname as FirstName
FROM person.businessentitycontact b
LEFT JOIN person.contacttype c on b.contacttypeid = c.contacttypeid
LEFT JOIN person.person p on b.businessentityid = p.businessentityid
WHERE c.name = 'Purchasing Manager'
ORDER BY lastname asc, firstname asc;
-------------------------------------------------------------------------------------------------------------------------------------------

-- Q7: From the following table sales.salesorderdetail  write a query in  SQL to retrieve the total cost of each salesorderID that exceeds 100000. 
-- Return SalesOrderID, total cost. Round to 2 decimal place and add the dollar sign at the front.

--Answer
Select * from sales.salesorderdetail;

SELECT * FROM sales.salesorderheader;

SELECT s.salesorderid as SalesOrderID, concat('$', round(h.totaldue,2)) as totalcost
FROM sales.salesorderdetail s
LEFT JOIN sales.salesorderheader h on s.salesorderid= h.salesorderid
WHERE h.totaldue >100000;


-------------------------------------------------------------------------------------------------------------------------------------------

-- Q8:From the following person.person table write a query in  SQL to retrieve those persons whose last name begins with letter 'R' and firstname end with 'n'. 
-- Return lastname, and firstname and display the result in ascending order on firstname and descending order on lastname columns.

--Answer

select lastname,firstname from person.person
where lastname like 'R%' 
AND firstname like '%n'
ORDER BY firstname asc, lastname desc;

-------------------------------------------------------------------------------------------------------------------------------------------

-- Q9: From the following humanresources.department table write a query in  SQL to skip the first 5 rows and return the next 5 rows from the sorted result set.

--Answer

select * from humanresources.department
offset 5 rows 
LIMIT 5;
-------------------------------------------------------------------------------------------------------------------------------------------

-- Q10:From the following tables write a query in  SQL to find the persons whose last name starts with letter 'L'. 
-- Return BusinessEntityID, FirstName, LastName, and PhoneNumber. Sort the result on lastname and firstname.

-- person.person, person.personphone

--Answer 

select * from person.person;
select * from person.personphone;

SELECT p.businessentityid as BusinessEntityID, 
p.firstname as FirstName, 
p.lastname as LastName, 
h.phonenumber as PhoneNumber
FROM person.person p
LEFT JOIN person.personphone h on p.businessentityid = h.businessentityid
WHERE p.lastname LIKE 'L%'

-------------------------------------------------------------------------------------------------------------------------------------------