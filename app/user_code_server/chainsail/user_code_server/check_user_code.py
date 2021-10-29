from chainsail.common import import_from_user


def main():
    pdf, initial_states = import_from_user()

    pdf.log_prob(initial_states)
    pdf.log_prob_gradient(initial_states)


if __name__ == "__main__":
    main()
