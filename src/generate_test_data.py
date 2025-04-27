import argparse
import random
import math

def generate_test_data(line_length, num_clusters, rounds, lines_per_round, max_angle, max_distance):
    """
    Generates test data for angle-based clustering.

    Args:
        line_length: Length of each line.
        num_clusters: Number of clusters.
        rounds: Number of expansion rounds.
        lines_per_round: Number of lines generated in each expansion round per cluster.
        max_angle: Maximum angle difference within a cluster.
        max_distance: Maximum distance between lines within a cluster.

    Returns:
        A list of lines, where each line is represented as a list containing
        [start_x, start_y, end_x, end_y, angle].
    """
    lines = []
    for cluster_index in range(num_clusters):
        angle = cluster_index  * (2 * max_angle + 1)
        for round_index in range(rounds):
            start_x, start_y = round_index * max_distance, 0
            end_x, end_y = generate_line_end(start_x, start_y, angle, line_length)
            lines.append([start_x, start_y, end_x, end_y, angle])
            for _ in range(lines_per_round - 1):
                new_start_x, new_start_y, new_end_x, new_end_y, angle_obtained = generate_line_within_limits(start_x, start_y, end_x, end_y, max_angle, max_distance, angle, line_length)
                lines.append([new_start_x, new_start_y, new_end_x, new_end_y, angle_obtained])
    return lines

def generate_line_end(start_x, start_y, angle, line_length):
    end_x = start_x + line_length * math.cos(math.radians(angle))
    end_y = start_y + line_length * math.sin(math.radians(angle))
    return end_x, end_y

def generate_line_within_limits(start_x, start_y, end_x, end_y, max_angle, max_distance, angle, line_length):
    new_angle = random.uniform(angle - max_angle + 1e-6, angle + max_angle - 1e-6)
    new_start_x, new_start_y = random_point_near_line(start_x, start_y, end_x, end_y, max_distance, line_length)
    end_x, end_y = generate_line_end(new_start_x, new_start_y, new_angle, line_length)
    return new_start_x, new_start_y, end_x, end_y, new_angle

def random_point_near_line(start_x, start_y, end_x, end_y, max_dist, line_length):
    
    #get a random "seed point" along the line
    r = random.uniform(0, line_length)
    theta = math.atan2(end_y - start_y, end_x - start_x)
    new_x_seed = start_x + r * math.cos(theta)
    new_y_seed = start_y + r * math.sin(theta)

    # Generate a random angle for the offset
    offset_angle = random.uniform(0, 2 * math.pi)

    # Calculate the offset distance within max_dist
    offset_dist = random.uniform(0, max_dist)

    # Calculate the final point's coordinates with the offset
    final_x = new_x_seed + offset_dist * math.cos(offset_angle)
    final_y = new_y_seed + offset_dist * math.sin(offset_angle)
    return final_x, final_y


def main():
    parser = argparse.ArgumentParser(description="Generate test data for angle-based clustering")
    parser.add_argument("-o", "--output_file", type=str, required=True, help="Path to output file")
    parser.add_argument("-l", "--line_length", type=float, required=True, help="Length of each line")
    parser.add_argument("-n", "--num_clusters", type=int, required=True, help="Number of clusters")
    parser.add_argument("-r", "--rounds", type=int, required=True, help="Number of lines in initial clustering round")
    parser.add_argument("-p", "--lines_per_round", type=int, required=True, help="Number of lines per expansion round")
    parser.add_argument("-a", "--max_angle", type=float, required=True, help="Maximum angle difference within a cluster")
    parser.add_argument("-d", "--max_distance", type=float, required=True, help="Maximum distance between lines within a cluster")

    args = parser.parse_args()

    lines = generate_test_data(args.line_length, args.num_clusters, args.rounds,
                               args.lines_per_round, args.max_angle, args.max_distance)

    with open(args.output_file, "w") as output_file:
        for i, line in enumerate(lines):
            output_file.write(f"{i}_{line[4]} 1 {line[0]} {line[1]} {line[2]} {line[3]}\n")

if __name__ == "__main__":
    main()
