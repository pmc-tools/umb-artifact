# Builds the artifact image with the tool versions of the paper:
#
#   docker buildx bake
#
# First the UMB Observatory (fetched from GitHub at a fixed commit, unchanged) is built from source with the versions below,
# then the artifact image (docker/Dockerfile) on top of it.

group "default" {
  targets = ["artifact"]
}

target "observatory" {
  context = "https://github.com/pmc-tools/umb-observatory.git#5dc44c954b7714ba08184346ba0ab28d1905385c"
  tags    = ["umb-observatory:tacas27"]
  args = {
    FLAVOR            = "source"
    # Storm build environment, the version current at the Storm commit below
    SOURCE_BASE_IMAGE = "movesrwth/storm-dependencies:20261009@sha256:e19b11b2fc772538eeb20f772193df20299c6a136caa2cb13ae40f4d6f3ce525"
    # Storm 1.14.0 + 68 commits (2026-10-12)
    storm_ref         = "2c6a7c2e96f7d64179d8193f27cea88f2cd19362"
    no_threads        = "12"
    # PRISM 4.11 + 1 commit
    PRISM_REF         = "f118f0b2706d0deed1f57b4110fbeb01e4142366"
    # mcsta: v3.1.311 of the paper can no longer be downloaded
    MODEST_VERSION    = "v3.1.315-g5c27830737"
    UMBI_SPEC         = "umbi==0.2.15"
    REGRESSION_REF    = "22da8d6ed73ab3b00f9324a0639d86f1d36e30c0"
  }
}

target "artifact" {
  context    = "."
  dockerfile = "docker/Dockerfile"
  contexts = { "umb-observatory:tacas27" = "target:observatory" }
  args     = { OBSERVATORY_IMAGE = "umb-observatory:tacas27" }
  tags     = ["umb-artifact"]
}
