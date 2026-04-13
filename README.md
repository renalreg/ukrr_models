<a name="readme-top"></a>

<div align='center'>

[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

</div>
<br />
<h1 align="center">UKRR Models</h1>

## About The Project

A limited set of database models for the RR database
<br/>

## Usage

```
poetry add ukrr_models
```

## Built With

[![SQLAlchemy][SQLAlchemy]][SQLAlchemy-url] 

## Utils quick guide 

### Deleting patient 

Delete patient with the specified rr_no from the database.

```
python ukrr_models/utils.py delete --rrno {rr_no} --username {username} --authorised-by {authorised_by} --reason {reason}
```

### Merge patient 

Move entries in the table for one patient into another.

```
python ukrr_models/utils.py merge --rrno 123456789 --destination-rrno 123456790
```

### Undelete patient

Check DELETED_PATIENTS table and re-construct the deleted patient back using data in the AUDIT tables.

```
python ukrr_models/utils.py undelete --rrno 123456789 --update
```

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Renal Registry 
* Website - [The UK Kidney Association](https://ukkidney.org/)
* X - [@UKKidney](https://twitter.com/@UKKidney)
* E-mail -  rrsystems@renalregistry.nhs.uk

Project Link - [https://github.com/renalreg/ukrr_models](https://github.com/renalreg/ukrr_models)

<br />

<p align="right">(<a href="#readme-top">back to top</a>)</p>

[issues-shield]: https://img.shields.io/github/issues/renalreg/ukrr_models.svg?style=for-the-badge
[issues-url]: https://github.com/renalreg/ukrr_models/issues
[license-shield]: https://img.shields.io/github/license/renalreg/ukrr_models.svg?style=for-the-badge
[license-url]: https://github.com/renalreg/ukrr_models/blob/master/LICENSE
[SQLAlchemy]: https://img.shields.io/badge/sqlalchemy-V1.4-D71F00?style=for-the-badge&logoColor=white
[SQLAlchemy-url]: https://www.sqlalchemy.org/
