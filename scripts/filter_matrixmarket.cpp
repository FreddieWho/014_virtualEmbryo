// One-pass, metadata-mask-only MatrixMarket column filter.
// This helper does not normalize, aggregate, or inspect expression values.
#include <charconv>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

static bool is_comment_or_empty(const std::string& line) {
    return line.empty() || line[0] == '%';
}

static bool parse_integer(const char*& begin, const char* end, std::int64_t& value) {
    while (begin < end && *begin == ' ') ++begin;
    auto result = std::from_chars(begin, end, value);
    if (result.ec != std::errc()) return false;
    begin = result.ptr;
    return true;
}

int main(int argc, char** argv) {
    if (argc != 4) {
        std::cerr << "usage: filter_matrixmarket SOURCE DEST MASK\n";
        return 2;
    }
    const fs::path source(argv[1]);
    const fs::path destination(argv[2]);
    const fs::path mask_path(argv[3]);

    std::ifstream mask_in(mask_path);
    if (!mask_in) {
        std::cerr << "cannot open mask: " << mask_path << "\n";
        return 3;
    }
    std::int64_t ncols = 0;
    std::int64_t nselected = 0;
    if (!(mask_in >> ncols >> nselected) || ncols < 1 || nselected < 0 || nselected > ncols) {
        std::cerr << "invalid mask header\n";
        return 4;
    }
    std::vector<unsigned char> keep(static_cast<std::size_t>(ncols) + 1, 0);
    for (std::int64_t i = 1; i <= ncols; ++i) {
        int bit = 0;
        if (!(mask_in >> bit) || (bit != 0 && bit != 1)) {
            std::cerr << "invalid mask value at column " << i << "\n";
            return 5;
        }
        keep[static_cast<std::size_t>(i)] = static_cast<unsigned char>(bit);
    }
    std::vector<std::int64_t> new_column(static_cast<std::size_t>(ncols) + 1, -1);
    std::int64_t next_column = 1;
    for (std::int64_t i = 1; i <= ncols; ++i) {
        if (keep[static_cast<std::size_t>(i)]) new_column[static_cast<std::size_t>(i)] = next_column++;
    }

    std::ifstream input(source);
    if (!input) {
        std::cerr << "cannot open source: " << source << "\n";
        return 6;
    }
    std::string line;
    if (!std::getline(input, line) || line != "%%MatrixMarket matrix coordinate integer general") {
        std::cerr << "unsupported MatrixMarket header\n";
        return 7;
    }
    std::int64_t nrows = 0;
    std::int64_t source_cols = 0;
    std::int64_t source_nnz = 0;
    while (std::getline(input, line)) {
        if (is_comment_or_empty(line)) continue;
        const char* begin = line.data();
        const char* end = begin + line.size();
        if (!parse_integer(begin, end, nrows) || !parse_integer(begin, end, source_cols) ||
            !parse_integer(begin, end, source_nnz) || nrows < 1 || source_cols != ncols) {
            std::cerr << "invalid MatrixMarket dimensions\n";
            return 8;
        }
        break;
    }
    if (nrows < 1 || source_nnz < 0) {
        std::cerr << "missing MatrixMarket dimensions\n";
        return 9;
    }

    fs::create_directories(destination.parent_path());
    const fs::path partial = destination.string() + ".partial";
    std::error_code ec;
    fs::remove(partial, ec);
    std::ofstream output(partial, std::ios::binary | std::ios::trunc);
    if (!output) {
        std::cerr << "cannot create destination: " << partial << "\n";
        return 10;
    }
    output << "%%MatrixMarket matrix coordinate integer general\n";
    output << nrows << ' ' << nselected << ' ';
    const std::streampos nnz_position = output.tellp();
    output << std::setw(20) << std::setfill('0') << 0 << std::setfill(' ') << '\n';

    std::int64_t selected_nnz = 0;
    while (std::getline(input, line)) {
        if (is_comment_or_empty(line)) continue;
        const char* begin = line.data();
        const char* end = begin + line.size();
        std::int64_t row = 0;
        std::int64_t column = 0;
        if (!parse_integer(begin, end, row) || !parse_integer(begin, end, column) ||
            row < 1 || row > nrows || column < 1 || column > source_cols) {
            std::cerr << "invalid MatrixMarket entry\n";
            output.close();
            fs::remove(partial, ec);
            return 11;
        }
        if (keep[static_cast<std::size_t>(column)]) {
            while (begin < end && (*begin == ' ' || *begin == '\t')) ++begin;
            output << row << ' ' << new_column[static_cast<std::size_t>(column)] << ' ';
            output.write(begin, static_cast<std::streamsize>(end - begin));
            output << '\n';
            ++selected_nnz;
        }
    }
    if (selected_nnz < 0 || selected_nnz > source_nnz) {
        std::cerr << "invalid selected nnz\n";
        output.close();
        fs::remove(partial, ec);
        return 12;
    }
    output.flush();
    output.seekp(nnz_position);
    output << std::setw(20) << std::setfill('0') << selected_nnz << std::setfill(' ');
    output.close();
    if (!output) {
        std::cerr << "failed writing destination\n";
        fs::remove(partial, ec);
        return 13;
    }
    fs::remove(destination, ec);
    fs::rename(partial, destination, ec);
    if (ec) {
        std::cerr << "cannot publish destination: " << ec.message() << "\n";
        fs::remove(partial, ec);
        return 14;
    }
    std::cout << nrows << ' ' << nselected << ' ' << selected_nnz << '\n';
    return 0;
}
