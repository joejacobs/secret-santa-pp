# -*- coding: utf-8 -*-
import argparse
import getpass
import io
import json
import os

from emailer import Emailer
from messageconstructor import MessageConstructor
from secretsantagraph import SecretSantaGraph


def argument_parser():
    p = argparse.ArgumentParser(
        description=(
            "Generate secret santa pairings "
            "and send everyone notification "
            "emails."
        )
    )
    p.add_argument("n_recipients", type=int, help="Number of recipients per gifter")
    p.add_argument(
        "people_data_json",
        type=str,
        help="Path to a JSON file containing participant json data",
    )
    p.add_argument(
        "-cl",
        "--low-prob-criteria",
        type=str,
        help=(
            "Path to a headerless CSV file containing the " "low-probability criteria"
        ),
    )
    p.add_argument(
        "-cm",
        "--medium-prob-criteria",
        type=str,
        help=(
            "Path to a headerless CSV file containing the "
            "medium-probability criteria"
        ),
    )
    p.add_argument(
        "-cx",
        "--exclusion-criteria",
        type=str,
        help=("Path to a headerless CSV file containing the " "exclusion criteria"),
    )
    p.add_argument(
        "-ea",
        "--email-address",
        type=str,
        help="Email address used to send the notification emails",
    )
    p.add_argument(
        "-ehtml",
        "--email-html",
        type=str,
        help=(
            "Path to a HTML file containing the HTML version of "
            "the notification email message"
        ),
    )
    p.add_argument(
        "-em",
        "--email-message",
        type=str,
        help=("Path to a text file containing the notification " "email message"),
    )
    p.add_argument(
        "-en", "--email-sender", type=str, help="Name of the person sending the email"
    )
    p.add_argument(
        "-es",
        "--email-subject",
        type=str,
        help=("Path to a text file containing the notification " "email subject"),
    )
    p.add_argument(
        "-lc",
        "--limit-currency",
        type=str,
        help="The currency of the spending limit specified",
    )
    p.add_argument(
        "-ld",
        "--limit-display",
        type=str,
        help=(
            "The currencies in which to display the spending "
            "limit in the email, comma separated, no spaces"
        ),
    )
    p.add_argument("-lv", "--limit-value", type=int, help="Spending limit")
    p.add_argument(
        "-p",
        "--participants",
        type=str,
        help=("Path to a text file containing the list of " "participants"),
    )
    p.add_argument(
        "-ra",
        "--reply-address",
        type=str,
        help="Specify an email reply-to address if required",
    )
    p.add_argument(
        "-s",
        "--save-as",
        type=str,
        help=("Save the solution into the people data JSON file " "under this key"),
    )
    p.add_argument(
        "-sa", "--smtp-address", type=str, help="Address of the SMTP server to use"
    )
    p.add_argument(
        "-sp",
        "--smtp-port",
        type=int,
        default=587,
        help="Port to connect to on the SMTP server",
    )
    p.add_argument(
        "-su",
        "--smtp-username",
        type=str,
        help=(
            "Username for logging into the SMTP server, defaults "
            "to the email address if unspecified"
        ),
    )
    p.add_argument(
        "-v",
        "--visualise",
        dest="visualise_graph",
        action="store_true",
        help="Visualise graph",
    )

    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "-i",
        "--input-file",
        type=str,
        help=(
            "Load an existing solution from this file, no new "
            "solution will be generated"
        ),
    )
    g.add_argument(
        "-o",
        "--output-file",
        type=str,
        help="Generate a solution and write it to this file",
    )

    p.set_defaults(visualise_graph=False)

    return p


def load_criteria(fpath):
    out_lst = []

    with io.open(fpath, mode="r", encoding="utf-8") as fp:
        for x in fp.read().strip().split("\n"):
            criterion = tuple([y.strip() for y in x.strip().split(",")])
            assert len(criterion) == 2
            out_lst.append(criterion)

    return out_lst


def main():
    # define command line arguments
    p = argument_parser()
    args = p.parse_args()

    print("Load people data: {}".format(args.people_data_json))
    with io.open(args.people_data_json, mode="r", encoding="utf-8") as fp:
        people_data = json.load(fp)

    # load exclusion criteria from file
    exclusion = []

    if args.exclusion_criteria:
        print("Load exclusion criteria: {}".format(args.exclusion_criteria))
        exclusion = load_criteria(args.exclusion_criteria)

    # load low-probability criteria from file
    low_prob = []

    if args.low_prob_criteria:
        print("Load low-prob criteria: {}".format(args.low_prob_criteria))
        low_prob = load_criteria(args.low_prob_criteria)

    # load medium-probability criteria from file
    med_prob = []

    if args.medium_prob_criteria:
        print("Load med-prob criteria: {}".format(args.medium_prob_criteria))
        med_prob = load_criteria(args.medium_prob_criteria)

    print("Construct SecretSantaGraph object")
    ss_graph = SecretSantaGraph(
        people_data,
        args.n_recipients,
        exclusion_criteria=exclusion,
        low_prob_criteria=low_prob,
        medium_prob_criteria=med_prob,
    )

    if args.input_file:
        print("Load existing solution: {}".format(args.input_file))
        ss_graph.load_solution(args.input_file)
    elif args.output_file:
        assert not os.path.exists(args.output_file)

        with io.open(args.participants, mode="r", encoding="utf-8") as fp:
            print("Load participants list: {}".format(args.participants))
            participants = [x.strip() for x in fp.read().strip().split("\n")]

        print("Generate solution")
        ss_graph.run_solver(participants)

        print("Save solution to disk: {}".format(args.output_file))
        ss_graph.save_solution(args.output_file)

    if args.save_as:
        print("Add solution to people data under key: {}".format(args.save_as))
        new_people_data = ss_graph.add_to_people_data(args.save_as)

        print("Save new people data to disk: {}".format(args.people_data_json))
        with io.open(args.people_data_json, mode="w", encoding="utf-8") as fp:
            fp.write(json.dumps(new_people_data, indent=4, sort_keys=True))

    if args.visualise_graph:
        print("Visualise solution")
        ss_graph.draw_solution()

    if args.email_address:
        print("Send notification emails from: {}".format(args.email_address))
        assert args.email_message
        assert args.email_subject
        assert args.email_sender
        assert args.smtp_address

        limit_display = None

        if args.limit_value:
            assert args.limit_currency
            assert args.limit_display
            limit_display = args.limit_display.split(",")

        # get smtp username, defaulting to sender email if unspecified
        smtp_username = args.email_address

        if args.smtp_username:
            smtp_username = args.smtp_username

        # get smtp password from user
        smtp_password = getpass.getpass("Please input SMTP Password: ")

        # get reply-to address, defaulting to sender email if unspecified
        reply_address = args.email_address

        if args.reply_address:
            reply_address = args.reply_address

        print("Load email subject: {}".format(args.email_subject))
        with io.open(args.email_subject, mode="r", encoding="utf-8") as fp:
            sub_constructor = MessageConstructor(
                fp.read(), args.limit_value, args.limit_currency, limit_display
            )

        print("Load email message: {}".format(args.email_message))
        with io.open(args.email_message, mode="r", encoding="utf-8") as fp:
            msg_constructor = MessageConstructor(
                fp.read(), args.limit_value, args.limit_currency, limit_display
            )

        html_constructor = None

        if args.email_html:
            print("Load HTML email message: {}".format(args.email_html))
            with io.open(args.email_html, mode="r", encoding="utf-8") as fp:
                html_constructor = MessageConstructor(
                    fp.read(), args.limit_value, args.limit_currency, limit_display
                )

        # initialise the emailer
        print("Initialise emailer: {}:{}".format(args.smtp_address, args.smtp_port))
        emailer = Emailer(
            args.smtp_address,
            args.smtp_port,
            smtp_username,
            smtp_password,
            args.email_address,
            args.email_sender,
            reply_address,
            sub_constructor,
            msg_constructor,
            html_constructor,
        )

        for gifter, recipients in ss_graph.get_solution_arr():
            print("\tEmailing {}".format(gifter))
            emailer.send(gifter, people_data[gifter]["email"], recipients)


if __name__ == "__main__":
    main()
