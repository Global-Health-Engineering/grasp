from xml.dom import minidom
import csv
import os
import git


class Converter:
    def __init__(self, **kwargs) -> None:
        """
        main class function
        :param kwargs: input and output file required
        """
        input_file_name = kwargs.get("input_file")
        output_file_name = kwargs.get("output_file")

        if not input_file_name or not output_file_name:
            raise TypeError("You must specify an input and output file")

        input_file_abs_path = os.path.abspath(input_file_name)
        input_file_exists = os.path.exists(input_file_abs_path)

        if not input_file_exists:
            raise TypeError("The file %s does not exist." % input_file_name)

        input_extension = os.path.splitext(input_file_name)[1]

        if input_extension != ".gpx":
            raise TypeError("Input file must be a GPX file")

        output_extension = os.path.splitext(output_file_name)[1]

        if output_extension != ".csv":
            raise TypeError("Output file must be a CSV file")

        with open(input_file_abs_path, "r") as gpx_in:
            gpx_string = gpx_in.read()
            self.convert(gpx_string, output_file_name)

    def convert(self, gpx_string: str, output_file_name: str) -> None:
        """
        Core conversion method
        :param gpx_string: GPX XML data
        :param output_file_name: output file name
        :return:
        """
        mydoc = minidom.parseString(gpx_string)

        trkpt = mydoc.getElementsByTagName("trkpt")
        row_list = []

        columns = ["timestamp", "latitude", "longitude", "elevation"]

        # parse trackpoint elements.
        # Search for child elements in each trackpoint so they stay in sync.
        for elem in trkpt:
            etimestamp = elem.getElementsByTagName("time")
            timestamp = None
            for selem in etimestamp:
                timestamp = selem.firstChild.data

            lat = elem.attributes["lat"].value
            lng = elem.attributes["lon"].value

            eelevation = elem.getElementsByTagName("ele")
            elevation = None
            for selem in eelevation:
                elevation = selem.firstChild.data

            this_row = [timestamp, lat, lng, elevation]
            row_list.append(this_row)

        with open(output_file_name, "w") as output_file:
            writer = csv.writer(output_file)
            writer.writerow(columns)
            writer.writerows(row_list)


def get_git_root(path):
    git_repo = git.Repo(path, search_parent_directories=True)
    return git_repo.working_dir


def main():
    inpf = os.path.join(get_git_root(os.getcwd()),
                        "data",
                        "raw_data",
                        "testing",
                        "activity_17546190369.gpx")
    outf = os.path.join(get_git_root(os.getcwd()),
                        "data",
                        "derived_data",
                        "testing",
                        "activity_17546190369.csv")
    Converter(input_file=inpf, output_file=outf)


if __name__ == "__main__":
    main()
