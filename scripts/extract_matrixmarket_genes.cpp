// One-pass extraction of selected genes from a sanitized MatrixMarket object.
// It writes raw selected-gene counts and per-cell library sizes only.  No
// aggregation, normalization, or target comparison is performed here.
#include <charconv>
#include <cerrno>
#include <cstring>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

namespace fs = std::filesystem;

static bool skip_line(const std::string& line) {
    return line.empty() || line[0] == '%';
}

static bool integer_at(const char*& begin, const char* end, std::int64_t& value) {
    while (begin < end && (*begin == ' ' || *begin == '\t')) ++begin;
    auto result = std::from_chars(begin, end, value);
    if (result.ec != std::errc()) return false;
    begin = result.ptr;
    return true;
}

int main(int argc, char** argv) {
    if (argc != 5) {
        std::cerr << "usage: extract_matrixmarket_genes SOURCE MATRIX_OUT LIBSIZE_OUT ROWMAP\n";
        return 2;
    }
    const fs::path source(argv[1]);
    const fs::path matrix_out(argv[2]);
    const fs::path lib_out(argv[3]);
    const fs::path rowmap_path(argv[4]);

    std::ifstream rowmap_in(rowmap_path);
    if (!rowmap_in) { std::cerr << "cannot open row map\n"; return 3; }
    std::int64_t nrows = 0, nselected = 0;
    if (!(rowmap_in >> nrows >> nselected) || nrows < 1 || nselected < 1) {
        std::cerr << "invalid row map header\n"; return 4;
    }
    std::vector<std::int64_t> row_map(static_cast<std::size_t>(nrows) + 1, -1);
    for (std::int64_t i = 1; i <= nrows; ++i) {
        if (!(rowmap_in >> row_map[static_cast<std::size_t>(i)]) ||
            row_map[static_cast<std::size_t>(i)] >= nselected) {
            std::cerr << "invalid row map at row " << i << "\n"; return 5;
        }
    }

    std::ifstream input(source);
    if (!input) { std::cerr << "cannot open source\n"; return 6; }
    std::string line;
    if (!std::getline(input, line) || line != "%%MatrixMarket matrix coordinate integer general") {
        std::cerr << "unsupported MatrixMarket header\n"; return 7;
    }
    std::int64_t source_rows = 0, ncols = 0, source_nnz = 0;
    while (std::getline(input, line)) {
        if (skip_line(line)) continue;
        const char* begin = line.data();
        const char* end = begin + line.size();
        if (!integer_at(begin, end, source_rows) || !integer_at(begin, end, ncols) ||
            !integer_at(begin, end, source_nnz) || source_rows != nrows || ncols < 1) {
            std::cerr << "invalid MatrixMarket dimensions\n"; return 8;
        }
        break;
    }
    if (source_rows < 1 || ncols < 1 || source_nnz < 0) {
        std::cerr << "missing MatrixMarket dimensions\n"; return 9;
    }

    fs::create_directories(matrix_out.parent_path());
    fs::create_directories(lib_out.parent_path());
    const fs::path matrix_partial = matrix_out.string() + ".partial";
    const fs::path lib_partial = lib_out.string() + ".partial";
    std::error_code ec;
    fs::remove(matrix_partial, ec);
    fs::remove(lib_partial, ec);

    const std::uint64_t matrix_bytes = static_cast<std::uint64_t>(ncols) *
                                        static_cast<std::uint64_t>(nselected) * sizeof(float);
    int fd = ::open(matrix_partial.c_str(), O_RDWR | O_CREAT | O_TRUNC, 0660);
    if (fd < 0 || ::ftruncate(fd, static_cast<off_t>(matrix_bytes)) != 0) {
        std::cerr << "cannot allocate matrix output: " << std::strerror(errno) << "\n";
        if (fd >= 0) ::close(fd);
        return 10;
    }
    void* mapped = ::mmap(nullptr, matrix_bytes, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (mapped == MAP_FAILED) {
        std::cerr << "cannot map matrix output: " << std::strerror(errno) << "\n";
        ::close(fd); fs::remove(matrix_partial, ec); return 11;
    }
    auto* values = static_cast<float*>(mapped);
    std::memset(values, 0, matrix_bytes);
    std::vector<double> library_size(static_cast<std::size_t>(ncols), 0.0);
    std::int64_t seen = 0, selected_seen = 0;
    while (std::getline(input, line)) {
        if (skip_line(line)) continue;
        const char* begin = line.data();
        const char* end = begin + line.size();
        std::int64_t row = 0, column = 0;
        if (!integer_at(begin, end, row) || !integer_at(begin, end, column) ||
            row < 1 || row > nrows || column < 1 || column > ncols) {
            std::cerr << "invalid MatrixMarket entry row=" << row << " column=" << column << " line=" << line << "\n";
            ::munmap(mapped, matrix_bytes); ::close(fd); fs::remove(matrix_partial, ec); return 12;
        }
        while (begin < end && (*begin == ' ' || *begin == '\t')) ++begin;
        char* value_end = nullptr;
        errno = 0;
        const double value = std::strtod(begin, &value_end);
        if (value_end == begin || errno == ERANGE || value < 0.0) {
            std::cerr << "invalid MatrixMarket value\n";
            ::munmap(mapped, matrix_bytes); ::close(fd); fs::remove(matrix_partial, ec); return 13;
        }
        library_size[static_cast<std::size_t>(column - 1)] += value;
        const std::int64_t selected = row_map[static_cast<std::size_t>(row)];
        if (selected >= 0) {
            values[(static_cast<std::size_t>(column - 1) * static_cast<std::size_t>(nselected)) +
                   static_cast<std::size_t>(selected)] = static_cast<float>(value);
            ++selected_seen;
        }
        ++seen;
    }
    if (seen != source_nnz) {
        std::cerr << "entry count mismatch: saw " << seen << " expected " << source_nnz << "\n";
        ::munmap(mapped, matrix_bytes); ::close(fd); fs::remove(matrix_partial, ec); return 14;
    }
    if (::msync(mapped, matrix_bytes, MS_SYNC) != 0) {
        std::cerr << "matrix sync failed\n";
        ::munmap(mapped, matrix_bytes); ::close(fd); fs::remove(matrix_partial, ec); return 15;
    }
    ::munmap(mapped, matrix_bytes);
    ::close(fd);
    fs::remove(matrix_out, ec);
    fs::rename(matrix_partial, matrix_out, ec);
    if (ec) { std::cerr << "cannot publish matrix: " << ec.message() << "\n"; fs::remove(matrix_partial, ec); return 16; }

    std::ofstream lib_file(lib_partial, std::ios::binary | std::ios::trunc);
    if (!lib_file) { std::cerr << "cannot create library-size output\n"; return 17; }
    lib_file.write(reinterpret_cast<const char*>(library_size.data()),
                   static_cast<std::streamsize>(library_size.size() * sizeof(double)));
    lib_file.close();
    fs::remove(lib_out, ec);
    fs::rename(lib_partial, lib_out, ec);
    if (ec) { std::cerr << "cannot publish library sizes: " << ec.message() << "\n"; fs::remove(lib_partial, ec); return 18; }
    std::cout << ncols << ' ' << nselected << ' ' << seen << ' ' << selected_seen << '\n';
    return 0;
}
