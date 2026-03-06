from collections import UserDict
from datetime import datetime, timedelta
import pickle


# =========================
#       FIELD CLASSES
# =========================

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    """Телефон повинен складатися з рівно 10 цифр."""

    def __init__(self, value):
        self.validate(value)
        super().__init__(value)

    @staticmethod
    def validate(value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must contain exactly 10 digits")


class Birthday(Field):
    """Дата у форматі DD.MM.YYYY"""

    def __init__(self, value):
        try:
            parsed = datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(parsed)

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


# =========================
#        RECORD CLASS
# =========================

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                return
        raise ValueError("Phone not found")

    def edit_phone(self, old_phone, new_phone):
        for p in self.phones:
            if p.value == old_phone:
                p.value = Phone(new_phone).value
                return
        raise ValueError("Old phone not found")

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def days_to_birthday(self):
        if not self.birthday:
            return None

        today = datetime.today().date()
        bday = self.birthday.value.date().replace(year=today.year)

        if bday < today:
            bday = bday.replace(year=today.year + 1)

        return (bday - today).days

    def __str__(self):
        phones = "; ".join(p.value for p in self.phones)
        bday = f", birthday: {self.birthday}" if self.birthday else ""
        return f"Contact: {self.name.value}, phones: {phones}{bday}"


# =========================
#      ADDRESS BOOK
# =========================

class AddressBook(UserDict):

    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
        else:
            raise KeyError("Record not found")

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        next_week = today + timedelta(days=7)
        result = []

        for record in self.data.values():
            if record.birthday:
                bday = record.birthday.value.date().replace(year=today.year)

                if bday < today:
                    bday = bday.replace(year=today.year + 1)

                if today <= bday <= next_week:
                    result.append({
                        "name": record.name.value,
                        "congratulation_date": bday.strftime("%d.%m.%Y")
                    })

        return result


# =========================
#     SERIALIZATION
# =========================

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


# =========================
#     DECORATOR
# =========================

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Contact not found."
        except ValueError as e:
            return str(e)
        except IndexError:
            return "Not enough arguments."
    return inner


# =========================
#   COMMAND HANDLERS
# =========================

@input_error
def add_contact(args, book):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."

    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."

    record.add_phone(phone)
    return message


@input_error
def change_phone(args, book):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record is None:
        raise KeyError()
    record.edit_phone(old_phone, new_phone)
    return "Phone updated."


@input_error
def show_phone(args, book):
    name = args[0]
    record = book.find(name)
    if record:
        return "; ".join(p.value for p in record.phones)
    return "Contact not found."


def show_all(book):
    if not book.data:
        return "No contacts."
    return "\n".join(str(r) for r in book.values())


@input_error
def add_birthday(args, book):
    name, date = args
    record = book.find(name)
    if not record:
        raise KeyError()
    record.add_birthday(date)
    return "Birthday added."


@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    if not record:
        raise KeyError()
    if not record.birthday:
        return "Birthday not set."
    return str(record.birthday)


@input_error
def birthdays(args, book):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays next week."
    return "\n".join(
        f"{item['name']}: {item['congratulation_date']}"
        for item in upcoming
    )


# =========================
#     PARSE FUNCTION
# =========================

def parse_input(user_input):
    parts = user_input.strip().split()
    return parts[0].lower(), parts[1:]


# =========================
#         MAIN
# =========================

def main():

    # 🔹 Завантаження даних
    book = load_data()

    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)   # 🔹 Збереження перед виходом
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_phone(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
